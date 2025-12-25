import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
import chardet
import magic
from collections import Counter
import os

from config import settings
from utils.helpers import format_file_size, detect_language_from_extension

logger = logging.getLogger(__name__)


class FileReader:
    def __init__(self):
        self.max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        self.allowed_extensions = settings.ALLOWED_EXTENSIONS
        self.excluded_dirs = settings.EXCLUDED_DIRS
    
    async def read_repository(
        self,
        repo_path: Path,
        include_tests: bool = False
    ) -> Dict:
        logger.info(f"Reading repository at {repo_path}")
        
        files_data = []
        total_size = 0
        total_lines = 0
        language_counter = Counter()
        file_tree = {}
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [
                d for d in dirs
                if d not in self.excluded_dirs and not d.startswith('.')
            ]
            
            for file_name in files:
                file_path = Path(root) / file_name
                
                if not self._should_process_file(file_path, include_tests):
                    continue
                
                try:
                    file_info = await self._read_file(file_path, repo_path)
                    
                    if file_info:
                        files_data.append(file_info)
                        total_size += file_info['size']
                        total_lines += file_info['lines']
                        
                        language = file_info.get('language')
                        if language:
                            language_counter[language] += 1
                
                except Exception as e:
                    logger.warning(f"Failed to read file {file_path}: {e}")
                    continue
        
        primary_language = language_counter.most_common(1)[0][0] if language_counter else "Unknown"
        
        result = {
            "files": files_data,
            "total_files": len(files_data),
            "total_size": total_size,
            "total_lines": total_lines,
            "languages": dict(language_counter),
            "primary_language": primary_language,
            "file_tree": self._build_file_tree(files_data)
        }
        
        logger.info(
            f"Repository reading completed. Files: {len(files_data)}, "
            f"Size: {format_file_size(total_size)}, Lines: {total_lines}"
        )
        
        return result
    
    async def _read_file(self, file_path: Path, repo_path: Path) -> Optional[Dict]:
        try:
            file_size = file_path.stat().st_size
            
            if file_size > self.max_file_size:
                logger.debug(f"Skipping large file: {file_path} ({format_file_size(file_size)})")
                return None
            
            if file_size == 0:
                return None
            
            relative_path = file_path.relative_to(repo_path)
            
            content = await self._read_file_content(file_path)
            
            if content is None:
                return None
            
            lines = content.count('\n') + 1
            
            language = detect_language_from_extension(file_path.suffix)
            
            file_type = self._categorize_file(file_path)
            
            return {
                "path": str(relative_path),
                "name": file_path.name,
                "extension": file_path.suffix,
                "size": file_size,
                "lines": lines,
                "content": content,
                "language": language,
                "type": file_type
            }
        
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    async def _read_file_content(self, file_path: Path) -> Optional[str]:
        try:
            loop = asyncio.get_event_loop()
            
            def read_sync():
                with open(file_path, 'rb') as f:
                    raw_content = f.read()
                
                if self._is_binary(raw_content):
                    return None
                
                detected = chardet.detect(raw_content)
                encoding = detected.get('encoding', 'utf-8')
                
                if encoding is None:
                    encoding = 'utf-8'
                
                try:
                    return raw_content.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    try:
                        return raw_content.decode('utf-8', errors='ignore')
                    except Exception:
                        return raw_content.decode('latin-1', errors='ignore')
            
            return await loop.run_in_executor(None, read_sync)
        
        except Exception as e:
            logger.error(f"Failed to read file content: {e}")
            return None
    
    def _is_binary(self, content: bytes) -> bool:
        if len(content) == 0:
            return False
        
        textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
        
        sample = content[:8192]
        
        non_text = sample.translate(None, textchars)
        
        if len(non_text) / len(sample) > 0.3:
            return True
        
        return False
    
    def _should_process_file(self, file_path: Path, include_tests: bool) -> bool:
        if file_path.name.startswith('.'):
            return False
        
        if any(excluded in file_path.parts for excluded in self.excluded_dirs):
            return False
        
        if not include_tests:
            if 'test' in file_path.name.lower() or 'spec' in file_path.name.lower():
                return False
            if any('test' in part.lower() for part in file_path.parts):
                return False
        
        extension = file_path.suffix.lower()
        
        if extension in self.allowed_extensions:
            return True
        
        if file_path.name in ["Dockerfile", "Makefile", "README", ".gitignore", ".dockerignore"]:
            return True
        
        return False
    
    def _categorize_file(self, file_path: Path) -> str:
        extension = file_path.suffix.lower()
        name = file_path.name.lower()
        
        if extension in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.cpp', '.c', '.cs', '.rb', '.php', '.swift', '.kt', '.scala']:
            return "code"
        
        if extension in ['.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.env']:
            return "config"
        
        if extension in ['.md', '.txt', '.rst'] or 'readme' in name:
            return "documentation"
        
        if 'test' in name or 'spec' in name:
            return "test"
        
        if extension in ['.html', '.css', '.scss', '.sass', '.less']:
            return "frontend"
        
        if extension in ['.sql']:
            return "database"
        
        if 'dockerfile' in name or 'makefile' in name or extension in ['.sh']:
            return "devops"
        
        return "other"
    
    def _build_file_tree(self, files_data: List[Dict]) -> Dict:
        tree = {}
        
        for file_info in files_data:
            path_parts = Path(file_info['path']).parts
            current = tree
            
            for i, part in enumerate(path_parts):
                if i == len(path_parts) - 1:
                    current[part] = {
                        "type": "file",
                        "size": file_info['size'],
                        "lines": file_info['lines'],
                        "language": file_info['language']
                    }
                else:
                    if part not in current:
                        current[part] = {"type": "directory", "children": {}}
                    current = current[part]["children"]
        
        return tree
    
    async def get_file_statistics(self, files_data: List[Dict]) -> Dict:
        stats = {
            "total_files": len(files_data),
            "by_type": Counter(),
            "by_language": Counter(),
            "largest_files": [],
            "longest_files": []
        }
        
        for file_info in files_data:
            stats["by_type"][file_info['type']] += 1
            if file_info.get('language'):
                stats["by_language"][file_info['language']] += 1
        
        sorted_by_size = sorted(files_data, key=lambda x: x['size'], reverse=True)
        stats["largest_files"] = [
            {"path": f['path'], "size": f['size']}
            for f in sorted_by_size[:10]
        ]
        
        sorted_by_lines = sorted(files_data, key=lambda x: x['lines'], reverse=True)
        stats["longest_files"] = [
            {"path": f['path'], "lines": f['lines']}
            for f in sorted_by_lines[:10]
        ]
        
        return stats