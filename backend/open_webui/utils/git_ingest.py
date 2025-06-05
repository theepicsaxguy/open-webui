import os
import subprocess
import tempfile
import fnmatch
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from gitingest.repository_ingest import ingest_async

log = logging.getLogger(__name__)

@dataclass
class FileSystemNode:
    name: str
    full_path: str
    node_type: str  # 'file' or 'directory'
    size: int = 0
    content: Optional[str] = None
    children: List['FileSystemNode'] = field(default_factory=list)


def clone_repo(url: str, branch: str | None = None, commit: str | None = None) -> str:
    """Clone a git repository and optionally checkout a branch or commit."""
    tmp_dir = tempfile.mkdtemp(prefix="git_ingest_")
    args = ["git", "clone", url, tmp_dir]
    if branch:
        args.extend(["--branch", branch])
    subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if commit:
        subprocess.run(["git", "-C", tmp_dir, "checkout", commit], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return tmp_dir


def _should_include(name: str, include_patterns: list[str] | None, exclude_patterns: list[str] | None) -> bool:
    if exclude_patterns:
        for pat in exclude_patterns:
            if fnmatch.fnmatch(name, pat):
                return False
    if include_patterns:
        for pat in include_patterns:
            if fnmatch.fnmatch(name, pat):
                return True
        return False
    return True


def _read_file(path: str, max_file_size: int) -> Optional[str]:
    try:
        with open(path, "rb") as f:
            data = f.read(max_file_size + 1)
            if len(data) > max_file_size:
                return None
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                return None
            sample = text[:1000]
            non_printable = sum(1 for c in sample if ord(c) < 32 and c not in "\r\n\t")
            if len(sample) > 0 and non_printable / len(sample) > 0.1:
                return None
            return text
    except Exception as exc:
        log.warning("Failed to read %s: %s", path, exc)
        return None


def traverse_directory(
    root_path: str,
    max_depth: int = 20,
    max_file_size: int = 10_485_760,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
    ingest_content: bool = True,
    _depth: int = 0,
) -> FileSystemNode:
    node = FileSystemNode(os.path.basename(root_path) or root_path, os.path.abspath(root_path), "directory")
    if _depth > max_depth:
        return node
    try:
        for entry in sorted(os.scandir(root_path), key=lambda e: e.name):
            if entry.is_dir(follow_symlinks=False):
                if _should_include(entry.name, include_patterns, exclude_patterns):
                    child = traverse_directory(
                        entry.path,
                        max_depth,
                        max_file_size,
                        include_patterns,
                        exclude_patterns,
                        ingest_content,
                        _depth + 1,
                    )
                    node.children.append(child)
            elif entry.is_file(follow_symlinks=False):
                if _should_include(entry.name, include_patterns, exclude_patterns) and entry.stat().st_size <= max_file_size:
                    content = _read_file(entry.path, max_file_size) if ingest_content else None
                    node.children.append(
                        FileSystemNode(entry.name, entry.path, "file", entry.stat().st_size, content)
                    )
    except PermissionError as exc:
        log.warning("Permission denied accessing %s: %s", root_path, exc)
    return node


def _count_files(node: FileSystemNode) -> int:
    count = 1 if node.node_type == "file" else 0
    for child in node.children:
        count += _count_files(child)
    return count


def _sum_size(node: FileSystemNode) -> int:
    size = node.size if node.node_type == "file" else 0
    for child in node.children:
        size += _sum_size(child)
    return size


def build_summary(node: FileSystemNode) -> str:
    return f"Ingested Directory: {node.name}\nTotal Files: {_count_files(node)}\nTotal Size: {_sum_size(node)} bytes"


def build_tree(node: FileSystemNode, prefix: str = "") -> str:
    lines = [prefix + node.name if prefix else node.name]
    for idx, child in enumerate(node.children):
        connector = "└── " if idx == len(node.children) - 1 else "├── "
        child_prefix = prefix + ("    " if idx == len(node.children) - 1 else "│   ")
        lines.append(prefix + connector + child.name)
        if child.node_type == "directory":
            lines.extend(build_tree(child, child_prefix).splitlines())
    return "\n".join(lines)


def gather_content(node: FileSystemNode) -> str:
    parts: list[str] = []
    if node.node_type == "file" and node.content is not None:
        parts.append(f"// File: {node.name}\n{node.content}\n")
    for child in node.children:
        parts.append(gather_content(child))
    return "".join(parts)


def collect_files(node: FileSystemNode) -> List[FileSystemNode]:
    """Return a flat list of all file nodes contained in ``node``."""
    files: List[FileSystemNode] = []
    if node.node_type == "file":
        files.append(node)
    for child in node.children:
        files.extend(collect_files(child))
    return files


async def ingest(
    source: str,
    branch: str | None = None,
    commit: str | None = None,
    subpath: str | None = None,
    max_depth: int = 20,
    ingest_file_content: bool = True,
    include_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
) -> dict:
    """Ingest a Git repository or local path using the gitingest library."""

    src = source
    if commit:
        src = f"{src}#{commit}"
    if subpath:
        if src.startswith("http://") or src.startswith("https://") or src.endswith(".git") or "@" in src:
            if not src.endswith("/"):
                src += "/"
            src += subpath
        else:
            src = os.path.join(src, subpath)

    summary, tree, content = await ingest_async(
        source=src,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        branch=branch,
    )

    if not ingest_file_content:
        content = ""

    return {"Summary": summary, "DirectoryTree": tree, "FileContent": content}
