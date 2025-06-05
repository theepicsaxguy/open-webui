import logging
from typing import List, Optional, Tuple

from gitingest.cloning import clone_repo
from gitingest.query_parsing import parse_query
from gitingest.filesystem_schema import FileSystemNode, FileSystemNodeType
from gitingest.ingestion import FileSystemStats, _process_node, apply_gitingest_file
from gitingest.output_formatters import format_directory, format_single_file

log = logging.getLogger(__name__)


def collect_files(node: FileSystemNode) -> List[FileSystemNode]:
    """Return a flat list of all file nodes contained in ``node``."""
    files: List[FileSystemNode] = []
    if node.type == FileSystemNodeType.FILE:
        files.append(node)
    for child in node.children:
        files.extend(collect_files(child))
    return files


async def _ingest_to_node(
    source: str,
    branch: str | None = None,
    commit: str | None = None,
    subpath: str | None = None,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> Tuple[FileSystemNode, str, str, str]:
    """Return the root FileSystemNode and formatted output for a source."""
    parsed = await parse_query(
        source=source,
        max_file_size=10 * 1024 * 1024,
        from_web=True,
        include_patterns=set(include_patterns) if include_patterns else None,
        ignore_patterns=set(exclude_patterns) if exclude_patterns else None,
    )

    if branch:
        parsed.branch = branch
    if commit:
        parsed.commit = commit
    if subpath:
        parsed.subpath = subpath

    if parsed.url:
        await clone_repo(parsed.extract_clone_config())

    target_path = parsed.local_path / parsed.subpath.lstrip("/")

    # Apply .gitingest ignore patterns if present
    apply_gitingest_file(parsed.local_path, parsed)

    if (parsed.type and parsed.type == "blob") or target_path.is_file():
        node = FileSystemNode(
            name=target_path.name,
            type=FileSystemNodeType.FILE,
            path_str=str(target_path.relative_to(parsed.local_path)),
            path=target_path,
            size=target_path.stat().st_size,
            file_count=1,
        )
        summary, tree, content = format_single_file(node, parsed)
        return node, summary, tree, content

    root = FileSystemNode(
        name=target_path.name or parsed.slug,
        type=FileSystemNodeType.DIRECTORY,
        path_str=str(target_path.relative_to(parsed.local_path))
        if target_path != parsed.local_path
        else ".",
        path=target_path,
    )

    stats = FileSystemStats()
    _process_node(root, parsed, stats)
    summary, tree, content = format_directory(root, parsed)
    return root, summary, tree, content


async def ingest(
    source: str,
    branch: str | None = None,
    commit: str | None = None,
    subpath: str | None = None,
    ingest_file_content: bool = True,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> dict:
    """Ingest a Git repository or local path using the gitingest library."""
    node, summary, tree, content = await _ingest_to_node(
        source=source,
        branch=branch,
        commit=commit,
        subpath=subpath,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
    )

    if not ingest_file_content:
        content = ""

    return {"Summary": summary, "DirectoryTree": tree, "FileContent": content, "_node": node}
