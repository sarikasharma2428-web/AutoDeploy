import logging
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest
)
import uuid

from config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        self.host = settings.QDRANT_HOST
        self.port = settings.QDRANT_PORT
        self.dimension = settings.EMBEDDING_DIMENSION
        self.client = None
        self._connect()
    
    def _connect(self):
        try:
            logger.info(f"Connecting to Qdrant at {self.host}:{self.port}")
            self.client = QdrantClient(host=self.host, port=self.port)
            logger.info("Successfully connected to Qdrant")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def create_collection(self, collection_name: str, overwrite: bool = False):
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            
            if exists and overwrite:
                logger.info(f"Deleting existing collection: {collection_name}")
                self.client.delete_collection(collection_name)
                exists = False
            
            if not exists:
                logger.info(f"Creating collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.dimension,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection {collection_name} created successfully")
            else:
                logger.info(f"Collection {collection_name} already exists")
        
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def insert_chunks(self, collection_name: str, chunks: List[Dict]) -> int:
        logger.info(f"Inserting {len(chunks)} chunks into collection {collection_name}")
        
        if not chunks:
            return 0
        
        points = []
        for chunk in chunks:
            embedding = chunk.get('embedding')
            if not embedding:
                logger.warning(f"Chunk {chunk.get('chunk_id')} has no embedding, skipping")
                continue
            
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    'chunk_id': chunk.get('chunk_id'),
                    'content': chunk.get('content'),
                    'file_path': chunk.get('file_path'),
                    'file_name': chunk.get('file_name'),
                    'language': chunk.get('language'),
                    'type': chunk.get('type'),
                    'start_line': chunk.get('start_line'),
                    'end_line': chunk.get('end_line'),
                    'metadata': chunk.get('metadata', {})
                }
            )
            points.append(point)
        
        batch_size = 100
        inserted_count = 0
        
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            try:
                self.client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
                inserted_count += len(batch)
                
                if (i + batch_size) % 500 == 0:
                    logger.info(f"Inserted {inserted_count}/{len(points)} points")
            
            except Exception as e:
                logger.error(f"Failed to insert batch {i}: {e}")
        
        logger.info(f"Successfully inserted {inserted_count} chunks")
        return inserted_count
    
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = None,
        score_threshold: float = None,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        if top_k is None:
            top_k = settings.RAG_TOP_K
        
        if score_threshold is None:
            score_threshold = settings.RAG_SCORE_THRESHOLD
        
        try:
            search_filter = None
            if filter_dict:
                conditions = []
                for key, value in filter_dict.items():
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                if conditions:
                    search_filter = Filter(must=conditions)
            
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=search_filter
            )
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result.id,
                    'score': result.score,
                    'chunk_id': result.payload.get('chunk_id'),
                    'content': result.payload.get('content'),
                    'file_path': result.payload.get('file_path'),
                    'file_name': result.payload.get('file_name'),
                    'language': result.payload.get('language'),
                    'type': result.payload.get('type'),
                    'start_line': result.payload.get('start_line'),
                    'end_line': result.payload.get('end_line'),
                    'metadata': result.payload.get('metadata', {})
                })
            
            logger.info(f"Found {len(formatted_results)} results for query")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_by_text(
        self,
        collection_name: str,
        query_text: str,
        embedder,
        top_k: int = None,
        score_threshold: float = None,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        query_vector = embedder.generate_single_embedding(query_text)
        
        return self.search(
            collection_name=collection_name,
            query_vector=query_vector,
            top_k=top_k,
            score_threshold=score_threshold,
            filter_dict=filter_dict
        )
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict]:
        try:
            info = self.client.get_collection(collection_name)
            return {
                'name': collection_name,
                'vectors_count': info.vectors_count,
                'points_count': info.points_count,
                'status': info.status
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None
    
    def delete_collection(self, collection_name: str):
        try:
            logger.info(f"Deleting collection: {collection_name}")
            self.client.delete_collection(collection_name)
            logger.info(f"Collection {collection_name} deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
    
    def list_collections(self) -> List[str]:
        try:
            collections = self.client.get_collections().collections
            return [c.name for c in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []