import asyncio
import shutil
import logging
from pathlib import Path
from typing import Optional
import git
from git import Repo, GitCommandError
import aiofiles
import os

from config import settings
from utils.helpers import format_file_size, get_directory_size

logger = logging.getLogger(__name__)


class RepoCloner:
    def __init__(self):
        self.clone_dir = Path(settings.CLONE_DIR)
        self.clone_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = settings.MAX_REPO_SIZE_MB * 1024 * 1024
        self.clone_depth = settings.CLONE_DEPTH
        self.timeout = settings.CLONE_TIMEOUT
    
    async def clone_repository(
        self,
        repo_url: str,
        job_id: str,
        branch: str = "main"
    ) -> Path:
        target_path = self.clone_dir / job_id
        
        if target_path.exists():
            logger.warning(f"Directory {target_path} already exists. Removing it.")
            await self._remove_directory(target_path)
        
        target_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Cloning repository {repo_url} to {target_path}")
        
        try:
            await asyncio.wait_for(
                self._clone_with_timeout(repo_url, target_path, branch),
                timeout=self.timeout
            )
            
            repo_size = await get_directory_size(target_path)
            
            if repo_size > self.max_size_bytes:
                await self._remove_directory(target_path)
                raise ValueError(
                    f"Repository size ({format_file_size(repo_size)}) exceeds "
                    f"maximum allowed size ({settings.MAX_REPO_SIZE_MB}MB)"
                )
            
            logger.info(
                f"Successfully cloned repository. Size: {format_file_size(repo_size)}"
            )
            
            return target_path
        
        except asyncio.TimeoutError:
            logger.error(f"Clone operation timed out after {self.timeout} seconds")
            await self._remove_directory(target_path)
            raise TimeoutError(
                f"Repository cloning timed out after {self.timeout} seconds"
            )
        
        except GitCommandError as e:
            logger.error(f"Git command failed: {e}")
            await self._remove_directory(target_path)
            raise ValueError(f"Failed to clone repository: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error during cloning: {e}")
            await self._remove_directory(target_path)
            raise
    
    async def _clone_with_timeout(
        self,
        repo_url: str,
        target_path: Path,
        branch: str
    ):
        loop = asyncio.get_event_loop()
        
        def clone_sync():
            try:
                Repo.clone_from(
                    repo_url,
                    target_path,
                    depth=self.clone_depth,
                    branch=branch,
                    single_branch=True,
                    no_checkout=False
                )
            except GitCommandError as e:
                if "not found" in str(e).lower():
                    logger.info(f"Branch {branch} not found, trying default branch")
                    Repo.clone_from(
                        repo_url,
                        target_path,
                        depth=self.clone_depth,
                        single_branch=True
                    )
                else:
                    raise
        
        await loop.run_in_executor(None, clone_sync)
    
    async def get_repository_info(self, repo_path: Path) -> dict:
        try:
            repo = Repo(repo_path)
            
            commits = list(repo.iter_commits(max_count=1))
            latest_commit = commits[0] if commits else None
            
            branch = repo.active_branch.name if not repo.head.is_detached else "detached"
            
            remote_url = ""
            if repo.remotes:
                remote_url = repo.remotes.origin.url
            
            return {
                "branch": branch,
                "latest_commit": {
                    "sha": latest_commit.hexsha[:7] if latest_commit else None,
                    "message": latest_commit.message.strip() if latest_commit else None,
                    "author": str(latest_commit.author) if latest_commit else None,
                    "date": latest_commit.committed_datetime.isoformat() if latest_commit else None
                },
                "remote_url": remote_url
            }
        
        except Exception as e:
            logger.error(f"Failed to get repository info: {e}")
            return {}
    
    async def cleanup(self, job_id: str):
        target_path = self.clone_dir / job_id
        
        if target_path.exists():
            logger.info(f"Cleaning up repository at {target_path}")
            await self._remove_directory(target_path)
    
    async def _remove_directory(self, path: Path):
        loop = asyncio.get_event_loop()
        
        def remove_sync():
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
        
        await loop.run_in_executor(None, remove_sync)
    
    async def verify_repository(self, repo_path: Path) -> bool:
        try:
            repo = Repo(repo_path)
            return not repo.bare
        except Exception as e:
            logger.error(f"Repository verification failed: {e}")
            return False
    
    def get_excluded_patterns(self) -> list:
        return [
            f"*/{excluded_dir}/*" for excluded_dir in settings.EXCLUDED_DIRS
        ] + [
            "*.git/*",
            "*.pyc",
            "*.pyo",
            "*.so",
            "*.dylib",
            "*.dll",
            "*.exe",
            "*.bin",
            "*.jpg",
            "*.jpeg",
            "*.png",
            "*.gif",
            "*.bmp",
            "*.ico",
            "*.svg",
            "*.mp3",
            "*.mp4",
            "*.avi",
            "*.mov",
            "*.wmv",
            "*.pdf",
            "*.zip",
            "*.tar",
            "*.gz",
            "*.rar",
            "*.7z"
        ]
    
    async def get_file_count(self, repo_path: Path) -> int:
        count = 0
        excluded_patterns = self.get_excluded_patterns()
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [
                d for d in dirs
                if d not in settings.EXCLUDED_DIRS and not d.startswith('.')
            ]
            
            for file in files:
                file_path = Path(root) / file
                if self._should_include_file(file_path):
                    count += 1
        
        return count
    
    def _should_include_file(self, file_path: Path) -> bool:
        if file_path.name.startswith('.'):
            return False
        
        extension = file_path.suffix.lower()
        
        if not extension and file_path.name not in ["Dockerfile", "Makefile", "README"]:
            return False
        
        if extension in settings.ALLOWED_EXTENSIONS or file_path.name in settings.ALLOWED_EXTENSIONS:
            return True
        
        return False