import logging
from typing import List, Dict
import re
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)


class CodeChunker:
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
    
    def chunk_repository(self, files_data: List[Dict]) -> List[Dict]:
        logger.info(f"Starting chunking process for {len(files_data)} files")
        
        all_chunks = []
        
        for file_info in files_data:
            try:
                chunks = self._chunk_file(file_info)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Error chunking file {file_info.get('path')}: {e}")
                continue
        
        logger.info(f"Generated {len(all_chunks)} chunks from {len(files_data)} files")
        
        return all_chunks
    
    def _chunk_file(self, file_info: Dict) -> List[Dict]:
        content = file_info.get('content', '')
        file_path = file_info.get('path', '')
        language = file_info.get('language', '')
        
        if not content:
            return []
        
        if language in ['Python', 'JavaScript', 'TypeScript', 'Java', 'Go', 'C++', 'C#']:
            chunks = self._semantic_chunk(content, file_info)
        else:
            chunks = self._sliding_window_chunk(content, file_info)
        
        return chunks
    
    def _semantic_chunk(self, content: str, file_info: Dict) -> List[Dict]:
        chunks = []
        language = file_info.get('language', '')
        
        if language == 'Python':
            blocks = self._extract_python_blocks(content)
        elif language in ['JavaScript', 'TypeScript']:
            blocks = self._extract_js_blocks(content)
        elif language == 'Java':
            blocks = self._extract_java_blocks(content)
        else:
            blocks = self._extract_generic_blocks(content)
        
        for i, block in enumerate(blocks):
            if len(block['content']) < 50:
                continue
            
            chunk = {
                'chunk_id': f"{file_info.get('path')}::chunk_{i}",
                'content': block['content'],
                'file_path': file_info.get('path'),
                'file_name': file_info.get('name'),
                'language': file_info.get('language'),
                'type': block['type'],
                'start_line': block['start_line'],
                'end_line': block['end_line'],
                'metadata': {
                    'file_size': file_info.get('size'),
                    'total_lines': file_info.get('lines'),
                    'file_type': file_info.get('type')
                }
            }
            chunks.append(chunk)
        
        if not chunks and len(content) > 100:
            chunks = self._sliding_window_chunk(content, file_info)
        
        return chunks
    
    def _extract_python_blocks(self, content: str) -> List[Dict]:
        blocks = []
        lines = content.split('\n')
        
        class_pattern = re.compile(r'^class\s+\w+')
        function_pattern = re.compile(r'^def\s+\w+')
        
        current_block = None
        current_indent = 0
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            
            if class_pattern.match(stripped):
                if current_block:
                    blocks.append(current_block)
                current_block = {
                    'type': 'class',
                    'content': line + '\n',
                    'start_line': i + 1,
                    'end_line': i + 1
                }
                current_indent = indent
            
            elif function_pattern.match(stripped):
                if current_block and current_block['type'] == 'function':
                    blocks.append(current_block)
                if current_block and current_block['type'] == 'class' and indent > current_indent:
                    current_block['content'] += line + '\n'
                    current_block['end_line'] = i + 1
                else:
                    if current_block and current_block['type'] != 'class':
                        blocks.append(current_block)
                    current_block = {
                        'type': 'function',
                        'content': line + '\n',
                        'start_line': i + 1,
                        'end_line': i + 1
                    }
                    current_indent = indent
            
            elif current_block:
                if indent >= current_indent or stripped == '':
                    current_block['content'] += line + '\n'
                    current_block['end_line'] = i + 1
                else:
                    blocks.append(current_block)
                    current_block = None
        
        if current_block:
            blocks.append(current_block)
        
        if not blocks:
            blocks = [{
                'type': 'file',
                'content': content,
                'start_line': 1,
                'end_line': len(lines)
            }]
        
        return blocks
    
    def _extract_js_blocks(self, content: str) -> List[Dict]:
        blocks = []
        lines = content.split('\n')
        
        function_pattern = re.compile(r'(function\s+\w+|const\s+\w+\s*=\s*\(|class\s+\w+)')
        
        current_block = None
        brace_count = 0
        in_block = False
        
        for i, line in enumerate(lines):
            if function_pattern.search(line):
                if current_block and brace_count == 0:
                    blocks.append(current_block)
                current_block = {
                    'type': 'function',
                    'content': line + '\n',
                    'start_line': i + 1,
                    'end_line': i + 1
                }
                brace_count = line.count('{') - line.count('}')
                in_block = True
            
            elif in_block and current_block:
                current_block['content'] += line + '\n'
                current_block['end_line'] = i + 1
                brace_count += line.count('{') - line.count('}')
                
                if brace_count == 0:
                    blocks.append(current_block)
                    current_block = None
                    in_block = False
        
        if current_block:
            blocks.append(current_block)
        
        if not blocks:
            blocks = [{
                'type': 'file',
                'content': content,
                'start_line': 1,
                'end_line': len(lines)
            }]
        
        return blocks
    
    def _extract_java_blocks(self, content: str) -> List[Dict]:
        blocks = []
        lines = content.split('\n')
        
        class_pattern = re.compile(r'(public|private|protected)?\s*(class|interface|enum)\s+\w+')
        method_pattern = re.compile(r'(public|private|protected)?\s+\w+\s+\w+\s*\(')
        
        current_block = None
        brace_count = 0
        
        for i, line in enumerate(lines):
            if class_pattern.search(line):
                if current_block and brace_count == 0:
                    blocks.append(current_block)
                current_block = {
                    'type': 'class',
                    'content': line + '\n',
                    'start_line': i + 1,
                    'end_line': i + 1
                }
                brace_count = line.count('{') - line.count('}')
            
            elif method_pattern.search(line) and current_block:
                current_block['content'] += line + '\n'
                current_block['end_line'] = i + 1
                brace_count += line.count('{') - line.count('}')
            
            elif current_block:
                current_block['content'] += line + '\n'
                current_block['end_line'] = i + 1
                brace_count += line.count('{') - line.count('}')
                
                if brace_count == 0:
                    blocks.append(current_block)
                    current_block = None
        
        if current_block:
            blocks.append(current_block)
        
        if not blocks:
            blocks = [{
                'type': 'file',
                'content': content,
                'start_line': 1,
                'end_line': len(lines)
            }]
        
        return blocks
    
    def _extract_generic_blocks(self, content: str) -> List[Dict]:
        lines = content.split('\n')
        blocks = []
        
        current_block = {
            'type': 'section',
            'content': '',
            'start_line': 1,
            'end_line': 1
        }
        
        for i, line in enumerate(lines):
            current_block['content'] += line + '\n'
            current_block['end_line'] = i + 1
            
            if len(current_block['content']) >= self.chunk_size:
                blocks.append(current_block)
                overlap_lines = min(10, len(current_block['content'].split('\n')) // 4)
                overlap_content = '\n'.join(current_block['content'].split('\n')[-overlap_lines:])
                current_block = {
                    'type': 'section',
                    'content': overlap_content + '\n',
                    'start_line': i + 1 - overlap_lines,
                    'end_line': i + 1
                }
        
        if current_block['content'].strip():
            blocks.append(current_block)
        
        return blocks
    
    def _sliding_window_chunk(self, content: str, file_info: Dict) -> List[Dict]:
        chunks = []
        lines = content.split('\n')
        
        window_size = max(20, self.chunk_size // 50)
        overlap = max(5, self.chunk_overlap // 50)
        
        for i in range(0, len(lines), window_size - overlap):
            window_lines = lines[i:i + window_size]
            chunk_content = '\n'.join(window_lines)
            
            if len(chunk_content.strip()) < 50:
                continue
            
            chunk = {
                'chunk_id': f"{file_info.get('path')}::chunk_{i // (window_size - overlap)}",
                'content': chunk_content,
                'file_path': file_info.get('path'),
                'file_name': file_info.get('name'),
                'language': file_info.get('language'),
                'type': 'sliding_window',
                'start_line': i + 1,
                'end_line': min(i + window_size, len(lines)),
                'metadata': {
                    'file_size': file_info.get('size'),
                    'total_lines': file_info.get('lines'),
                    'file_type': file_info.get('type')
                }
            }
            chunks.append(chunk)
        
        return chunks
    
    def get_chunk_statistics(self, chunks: List[Dict]) -> Dict:
        if not chunks:
            return {}
        
        total_chunks = len(chunks)
        chunk_sizes = [len(chunk['content']) for chunk in chunks]
        
        return {
            'total_chunks': total_chunks,
            'average_chunk_size': sum(chunk_sizes) / total_chunks,
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'chunks_by_type': self._count_by_type(chunks),
            'chunks_by_language': self._count_by_language(chunks)
        }
    
    def _count_by_type(self, chunks: List[Dict]) -> Dict:
        type_counts = {}
        for chunk in chunks:
            chunk_type = chunk.get('type', 'unknown')
            type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
        return type_counts
    
    def _count_by_language(self, chunks: List[Dict]) -> Dict:
        lang_counts = {}
        for chunk in chunks:
            language = chunk.get('language', 'unknown')
            lang_counts[language] = lang_counts.get(language, 0) + 1
        return lang_counts