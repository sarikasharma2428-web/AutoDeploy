import json
import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
from uuid import uuid4

from config import settings
from services.chunker import CodeChunker
from services.embedder import Embedder
from services.file_reader import FileReader
from services.llm_engine import LLMEngine
from services.repo_cloner import RepoCloner
from services.vector_store import VectorStore
from utils.helpers import detect_build_tools, detect_framework, truncate_text

logger = logging.getLogger(__name__)


@dataclass
class SourceReference:
    id: str
    file_path: str
    start_line: int
    end_line: int
    snippet: str


class RepositoryAnalyzer:
    """Runs the full repo → embeddings → RAG → LLM pipeline."""

    def __init__(self) -> None:
        self.cloner = RepoCloner()
        self.file_reader = FileReader()
        self.chunker = CodeChunker()
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        self.llm_engine = LLMEngine()

    async def analyze_repo(
        self,
        repo_url: str,
        branch: str = "main",
        include_tests: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        job_id = uuid4().hex
        collection_name = f"repo_{job_id}"
        repo_path = None

        try:
            repo_path = await self.cloner.clone_repository(repo_url, job_id, branch)
            repo_git_info = await self.cloner.get_repository_info(repo_path)

            files_data = await self.file_reader.read_repository(
                repo_path, include_tests=include_tests
            )
            if not files_data.get("files"):
                raise ValueError("No analyzable files found in repository")

            chunks = self.chunker.chunk_repository(files_data["files"])
            if not chunks:
                raise ValueError("Unable to chunk repository content for embeddings")

            enriched_chunks = self.embedder.generate_embeddings(chunks)

            self.vector_store.create_collection(collection_name, overwrite=True)
            self.vector_store.insert_chunks(collection_name, enriched_chunks)

            references = self._collect_references(collection_name, enriched_chunks)
            analysis_payload = await self._generate_analysis_payload(
                repo_url=repo_url,
                branch=branch,
                metadata=metadata or {},
                repo_git_info=repo_git_info,
                files_data=files_data,
                references=references,
            )
            analysis_payload = self._normalize_payload(analysis_payload, references)

            result = {
                **analysis_payload,
                "metadata": {
                    "repo_url": repo_url,
                    "branch": branch,
                    "commit": repo_git_info.get("latest_commit", {}),
                    "total_files": files_data.get("total_files", 0),
                    "total_lines": files_data.get("total_lines", 0),
                    "languages": files_data.get("languages", {}),
                },
                "source_references": [asdict(ref) for ref in references],
            }

            return result

        finally:
            if repo_path:
                await self.cloner.cleanup(job_id)
            try:
                self.vector_store.delete_collection(collection_name)
            except Exception as exc:  # pragma: no cover - best effort cleanup
                logger.debug("Unable to drop Qdrant collection %s: %s", collection_name, exc)

    async def _generate_analysis_payload(
        self,
        repo_url: str,
        branch: str,
        metadata: Dict[str, Any],
        repo_git_info: Dict[str, Any],
        files_data: Dict[str, Any],
        references: List[SourceReference],
    ) -> Dict[str, Any]:
        context = self._build_context(repo_url, branch, files_data, references, repo_git_info)

        if self.llm_engine.is_available():
            logger.info("Generating structured analysis via %s", self.llm_engine.provider_name)
            response_text = await self.llm_engine.generate_structured_analysis(context)
            parsed = self._safe_parse_json(response_text)
            if parsed:
                return parsed
            logger.warning("LLM response was not valid JSON, falling back to heuristics")

        return self._fallback_analysis(files_data, references, repo_url, repo_git_info)

    def _build_context(
        self,
        repo_url: str,
        branch: str,
        files_data: Dict[str, Any],
        references: List[SourceReference],
        repo_git_info: Dict[str, Any],
    ) -> str:
        languages = ", ".join(
            f"{lang} ({count})" for lang, count in files_data.get("languages", {}).items()
        )
        reference_block = "\n".join(
            [
                f"[{ref.id}] {ref.file_path} ({ref.start_line}-{ref.end_line})\n{ref.snippet}"
                for ref in references
            ]
        )

        return f"""
Repository: {repo_url}
Branch: {branch}
Commit: {repo_git_info.get('latest_commit', {}).get('sha')}
Total files: {files_data.get('total_files', 0)}
Total lines: {files_data.get('total_lines', 0)}
Languages: {languages}

Key references:
{reference_block}
""".strip()

    def _collect_references(
        self, collection_name: str, chunks: List[Dict[str, Any]]
    ) -> List[SourceReference]:
        queries = [
            "main entrypoints and application setup",
            "security, secrets, or credentials",
            "infrastructure config files such as Dockerfile or terraform",
            "testing or ci configuration",
        ]

        selected: Dict[str, Dict[str, Any]] = {}

        for query in queries:
            try:
                hits = self.vector_store.search_by_text(
                    collection_name=collection_name,
                    query_text=query,
                    embedder=self.embedder,
                    top_k=3,
                    score_threshold=0.35,
                )
            except Exception as exc:  # pragma: no cover - connectivity
                logger.warning("Vector search failed for query '%s': %s", query, exc)
                hits = []

            for hit in hits:
                key = (
                    hit.get("file_path"),
                    hit.get("start_line"),
                    hit.get("end_line"),
                )
                if key not in selected:
                    selected[key] = hit

        if not selected:
            for chunk in chunks[:5]:
                key = (
                    chunk.get("file_path"),
                    chunk.get("start_line"),
                    chunk.get("end_line"),
                )
                selected[key] = chunk

        references = []
        for idx, chunk in enumerate(selected.values(), start=1):
            references.append(
                SourceReference(
                    id=f"ref-{idx}",
                    file_path=chunk.get("file_path") or chunk.get("file_name") or "unknown",
                    start_line=int(chunk.get("start_line") or 0),
                    end_line=int(chunk.get("end_line") or 0),
                    snippet=truncate_text(chunk.get("content", "").strip(), 500),
                )
            )

        return references[:10]

    def _fallback_analysis(
        self,
        files_data: Dict[str, Any],
        references: List[SourceReference],
        repo_url: str,
        repo_git_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        frameworks = detect_framework(files_data.get("files", []))
        build_tools = detect_build_tools(files_data.get("files", []))
        languages = list(files_data.get("languages", {}).keys())

        def ref_id_for_path(keyword: str) -> str:
            for ref in references:
                if keyword.lower() in ref.file_path.lower():
                    return ref.id
            return references[0].id if references else "ref-1"

        return {
            "summary": (
                f"Analyzed {files_data.get('total_files', 0)} files "
                f"({files_data.get('total_lines', 0)} LOC) across {repo_url}. "
                f"Primary languages: {', '.join(languages) or 'unknown'}."
            ),
            "summary_references": [ref.id for ref in references[:2]],
            "tech_stack": {
                "languages": languages,
                "frameworks": frameworks,
                "databases": [name for name in ("PostgreSQL", "SQLite", "MongoDB") if name.lower() in ''.join(languages).lower()],
                "tools": build_tools,
                "reference_ids": [ref.id for ref in references[:3]],
            },
            "security_findings": [
                {
                    "title": "Validate repository URLs",
                    "severity": "medium",
                    "description": "Ensure incoming repo URLs are validated and sanitized before cloning to avoid injections.",
                    "reference_id": ref_id_for_path("router"),
                }
            ],
            "code_smells": [
                {
                    "title": "Large configuration surface",
                    "impact": "medium",
                    "description": "Multiple configuration files detected. Consider consolidating defaults and documenting overrides.",
                    "reference_id": ref_id_for_path("config"),
                }
            ],
            "improvement_plan": [
                {
                    "title": "Add CI smoke tests",
                    "impact": "high",
                    "effort": "low",
                    "details": "Automate /api/repo/analyze smoke test for public repos.",
                    "reference_id": ref_id_for_path("tests"),
                }
            ],
            "devops_recommendations": [
                {
                    "title": "Harden container images",
                    "impact": "high",
                    "effort": "medium",
                    "details": "Use multi-stage builds and scan images before pushing.",
                    "reference_id": ref_id_for_path("Dockerfile"),
                }
            ],
        }

    @staticmethod
    def _safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _normalize_payload(
        payload: Dict[str, Any], references: List[SourceReference]
    ) -> Dict[str, Any]:
        ref_ids = [ref.id for ref in references] or ["ref-1"]

        def ensure_reference(entries: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
            normalized = []
            for entry in entries or []:
                if not isinstance(entry, dict):
                    continue
                if entry.get("reference_id") not in ref_ids:
                    entry["reference_id"] = ref_ids[0]
                normalized.append(entry)
            return normalized

        payload["summary_references"] = payload.get("summary_references") or ref_ids[:1]
        payload["security_findings"] = ensure_reference(payload.get("security_findings"))
        payload["code_smells"] = ensure_reference(payload.get("code_smells"))
        payload["improvement_plan"] = ensure_reference(payload.get("improvement_plan"))
        payload["devops_recommendations"] = ensure_reference(payload.get("devops_recommendations"))

        tech_stack = payload.get("tech_stack") or {}
        payload["tech_stack"] = {
            "languages": tech_stack.get("languages", []),
            "frameworks": tech_stack.get("frameworks", []),
            "databases": tech_stack.get("databases", []),
            "tools": tech_stack.get("tools", []),
            "reference_ids": tech_stack.get("reference_ids", ref_ids[:1]),
        }

        return payload

