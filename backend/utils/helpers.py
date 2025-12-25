import re
import os
import asyncio
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


def validate_github_url(url: str) -> bool:
    pattern = r'^https?://(?:www\.)?github\.com/[\w\-\.]+/[\w\-\.]+(?:\.git)?/?$'
    return bool(re.match(pattern, url))


def extract_repo_info(url: str) -> dict:
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    
    if len(path_parts) >= 2:
        owner = path_parts[0]
        repo = path_parts[1].replace('.git', '')
        return {
            "owner": owner,
            "repo": repo,
            "full_name": f"{owner}/{repo}"
        }
    
    return {}


def format_file_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


async def get_directory_size(path: Path) -> int:
    total_size = 0
    
    loop = asyncio.get_event_loop()
    
    def calculate_size():
        size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath):
                    size += os.path.getsize(filepath)
        return size
    
    total_size = await loop.run_in_executor(None, calculate_size)
    return total_size


def detect_language_from_extension(extension: str) -> Optional[str]:
    language_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'JavaScript React',
        '.tsx': 'TypeScript React',
        '.java': 'Java',
        '.go': 'Go',
        '.rs': 'Rust',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.c': 'C',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.cs': 'C#',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.m': 'Objective-C',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.sql': 'SQL',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.json': 'JSON',
        '.xml': 'XML',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.sass': 'Sass',
        '.less': 'Less',
        '.md': 'Markdown',
        '.rst': 'reStructuredText',
        '.txt': 'Text',
        '.toml': 'TOML',
        '.ini': 'INI',
        '.conf': 'Config',
    }
    
    return language_map.get(extension.lower())


def sanitize_filename(filename: str) -> str:
    sanitized = re.sub(r'[^\w\s\-\.]', '', filename)
    sanitized = re.sub(r'[\s]+', '_', sanitized)
    return sanitized[:255]


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def count_lines_of_code(content: str) -> dict:
    lines = content.split('\n')
    total_lines = len(lines)
    blank_lines = sum(1 for line in lines if not line.strip())
    comment_lines = sum(1 for line in lines if line.strip().startswith(('#', '//', '/*', '*', '--')))
    code_lines = total_lines - blank_lines - comment_lines
    
    return {
        "total": total_lines,
        "code": code_lines,
        "blank": blank_lines,
        "comment": comment_lines
    }


def parse_requirements_txt(content: str) -> list:
    packages = []
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            package = re.split(r'[><=!]', line)[0].strip()
            if package:
                packages.append(package)
    return packages


def parse_package_json(content: str) -> dict:
    import json
    try:
        data = json.loads(content)
        dependencies = list(data.get('dependencies', {}).keys())
        dev_dependencies = list(data.get('devDependencies', {}).keys())
        return {
            "name": data.get('name', ''),
            "version": data.get('version', ''),
            "dependencies": dependencies,
            "devDependencies": dev_dependencies
        }
    except json.JSONDecodeError:
        return {}


def detect_framework(files: list) -> list:
    frameworks = []
    
    file_names = [f.get('name', '') for f in files]
    file_contents = {f.get('name', ''): f.get('content', '') for f in files}
    
    if 'package.json' in file_names:
        content = file_contents.get('package.json', '')
        if 'react' in content.lower():
            frameworks.append('React')
        if 'vue' in content.lower():
            frameworks.append('Vue.js')
        if 'angular' in content.lower():
            frameworks.append('Angular')
        if 'next' in content.lower():
            frameworks.append('Next.js')
        if 'express' in content.lower():
            frameworks.append('Express.js')
    
    if 'requirements.txt' in file_names or 'pyproject.toml' in file_names:
        for file in files:
            content = file.get('content', '').lower()
            if 'django' in content:
                frameworks.append('Django')
            if 'flask' in content:
                frameworks.append('Flask')
            if 'fastapi' in content:
                frameworks.append('FastAPI')
    
    if 'pom.xml' in file_names or 'build.gradle' in file_names:
        frameworks.append('Spring Boot')
    
    if 'Gemfile' in file_names:
        content = file_contents.get('Gemfile', '')
        if 'rails' in content.lower():
            frameworks.append('Ruby on Rails')
    
    return list(set(frameworks))


def detect_build_tools(files: list) -> list:
    build_tools = []
    
    file_names = [f.get('name', '') for f in files]
    
    if 'Dockerfile' in file_names:
        build_tools.append('Docker')
    
    if 'docker-compose.yml' in file_names or 'docker-compose.yaml' in file_names:
        build_tools.append('Docker Compose')
    
    if 'Makefile' in file_names:
        build_tools.append('Make')
    
    if '.github' in str(file_names):
        build_tools.append('GitHub Actions')
    
    if '.gitlab-ci.yml' in file_names:
        build_tools.append('GitLab CI')
    
    if 'Jenkinsfile' in file_names:
        build_tools.append('Jenkins')
    
    if 'terraform' in str(file_names).lower():
        build_tools.append('Terraform')
    
    if 'kubernetes' in str(file_names).lower() or 'k8s' in str(file_names).lower():
        build_tools.append('Kubernetes')
    
    return list(set(build_tools))


def calculate_complexity_score(files_data: list) -> float:
    if not files_data:
        return 0.0
    
    total_complexity = 0
    
    for file_info in files_data:
        content = file_info.get('content', '')
        
        nesting_level = max(line.count('    ') for line in content.split('\n') if line.strip())
        
        control_structures = len(re.findall(r'\b(if|for|while|switch|case)\b', content))
        
        functions = len(re.findall(r'\b(def|function|func|public|private|protected)\s+\w+\s*\(', content))
        
        lines = file_info.get('lines', 0)
        
        file_complexity = (
            nesting_level * 2 +
            control_structures * 1.5 +
            functions * 0.5 +
            (lines / 100) * 0.1
        )
        
        total_complexity += file_complexity
    
    average_complexity = total_complexity / len(files_data)
    
    normalized_score = min(10.0, max(1.0, average_complexity))
    
    return round(normalized_score, 2)