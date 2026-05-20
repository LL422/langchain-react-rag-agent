import os
import subprocess
from utils.logger_handler import logger
from langchain_core.tools import tool
from rag.rag_service import RagSummarizeService
from rag.commit_history import commit_history_service
from utils.path_tool import get_project_root

rag = RagSummarizeService()

# Dynamic project root — can be changed at runtime via set_project_root()
_PROJECT_ROOT = get_project_root()


def set_project_root(path: str):
    """Change the working project root for all tools."""
    global _PROJECT_ROOT
    _PROJECT_ROOT = os.path.abspath(path)


def get_current_project_root() -> str:
    return _PROJECT_ROOT


def _safe_path(relative_path: str) -> str:
    """Resolve a path relative to current project root. Raises ValueError if outside."""
    resolved = os.path.normpath(os.path.join(_PROJECT_ROOT, relative_path))
    if not resolved.startswith(os.path.normpath(_PROJECT_ROOT)):
        raise ValueError(f"Access denied: path outside project root: {relative_path}")
    return resolved


@tool(description="Search the codebase using ripgrep. Returns matching lines with file paths and line numbers. Provide 'query' as the search term and optional 'file_pattern' to filter (e.g. '*.py', '*.ts').")
def search_codebase(query: str, file_pattern: str = "*") -> str:
    root = _PROJECT_ROOT
    try:
        cmd = ["rg", "--line-number", "--context=2", "--no-heading", query]
        if file_pattern and file_pattern != "*":
            cmd.extend(["--glob", file_pattern])
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=root, timeout=15)
        output = result.stdout.strip()
        if not output:
            return f"No matches found for '{query}'"
        lines = output.split("\n")
        if len(lines) > 60:
            output = "\n".join(lines[:60]) + f"\n\n... ({len(lines) - 60} more lines truncated)"
        return output
    except FileNotFoundError:
        logger.warning("[search_codebase] ripgrep not found, falling back to Python search")
        return _python_search(query, file_pattern)
    except subprocess.TimeoutExpired:
        return f"Search timed out for '{query}'. Try a more specific query."


def _python_search(query: str, file_pattern: str) -> str:
    results = []
    query_lower = query.lower()
    for root, dirs, dnames in os.walk(_PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules", "chroma_db", "logs", ".claude"}]
        for fname in dnames:
            if file_pattern != "*" and not fname.endswith(file_pattern.lstrip("*")):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if query_lower in line.lower():
                            rel = os.path.relpath(fpath, _PROJECT_ROOT)
                            results.append(f"{rel}:{i}: {line.strip()}")
            except Exception:
                continue
    if not results:
        return f"No matches found for '{query}'"
    if len(results) > 60:
        results = results[:60] + [f"... ({len(results) - 60} more matches)"]
    return "\n".join(results)


@tool(description="Read the contents of a file within the project. Provide 'path' (relative to project root). Optionally specify 'start_line' and 'end_line' to read a specific line range.")
def read_file(path: str, start_line: int = 0, end_line: int = 0) -> str:
    try:
        safe = _safe_path(path)
    except ValueError as e:
        return str(e)
    if not os.path.isfile(safe):
        return f"File not found: {path}"
    try:
        with open(safe, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        return f"Error reading file: {str(e)}"
    total = len(lines)
    if start_line > 0 and end_line > 0:
        start = max(0, start_line - 1)
        end = min(total, end_line)
        selected = lines[start:end]
    elif start_line > 0:
        start = max(0, start_line - 1)
        selected = lines[start:start + 50]
    else:
        selected = lines[:100]
    if len(selected) >= 100 and start_line == 0:
        result = "".join(selected) + f"\n\n... (file has {total} lines total, showing first 100)"
    else:
        result = "".join(selected)
        if end_line > 0 and end_line < total:
            result += f"\n... (shown lines {start_line}-{end_line} of {total})"
    return result


@tool(description="List files and subdirectories in a directory within the project. Provide 'path' (relative to project root). Returns file names, types, and sizes.")
def list_directory(path: str = ".") -> str:
    try:
        safe = _safe_path(path)
    except ValueError as e:
        return str(e)
    if not os.path.isdir(safe):
        return f"Directory not found: {path}"
    entries = []
    try:
        items = sorted(os.listdir(safe))
    except PermissionError:
        return f"Permission denied: {path}"
    for name in items:
        full = os.path.join(safe, name)
        rel = os.path.join(path, name) if path != "." else name
        if os.path.isdir(full):
            entries.append(f"  [DIR]  {rel}/")
        else:
            size = os.path.getsize(full)
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024 * 1024:
                size_str = f"{size // 1024}KB"
            else:
                size_str = f"{size // (1024 * 1024)}MB"
            entries.append(f"  [FILE] {rel} ({size_str})")
    if not entries:
        return f"Directory is empty: {path}"
    return "\n".join(entries[:80])


@tool(description="Show recent git commit history for the project. Provide 'n_commits' to specify how many recent commits to show (default 10). Returns one-line commit summaries.")
def git_history(n_commits: int = 10) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"-n{n_commits}"],
            capture_output=True, text=True, cwd=_PROJECT_ROOT, timeout=10
        )
        output = result.stdout.strip()
        if not output:
            return "No commits found in this repository."
        return f"Recent {n_commits} commits:\n{output}"
    except FileNotFoundError:
        return "Git is not installed or not available on this system."
    except subprocess.TimeoutExpired:
        return "Git command timed out."


@tool(description="Show git diff output. Provide 'target' like 'main..feature-branch', 'HEAD~3..HEAD', or leave empty for unstaged changes. Returns changed file list followed by the full diff.")
def git_diff(target: str = "") -> str:
    try:
        stat_cmd = ["git", "diff", "--stat"]
        diff_cmd = ["git", "diff"]
        if target:
            stat_cmd.append(target)
            diff_cmd.append(target)
        stat_result = subprocess.run(stat_cmd, capture_output=True, text=True, cwd=_PROJECT_ROOT, timeout=15)
        stat_output = stat_result.stdout.strip()
        if not stat_output:
            return "No changes detected."
        diff_result = subprocess.run(diff_cmd, capture_output=True, text=True, cwd=_PROJECT_ROOT, timeout=30)
        diff_output = diff_result.stdout.strip()
        max_lines = 150
        diff_lines = diff_output.split("\n")
        if len(diff_lines) > max_lines:
            diff_output = "\n".join(diff_lines[:max_lines]) + f"\n\n... ({len(diff_lines) - max_lines} more lines truncated)"
        return f"Changed files:\n{stat_output}\n\nDiff:\n{diff_output}"
    except FileNotFoundError:
        return "Git is not installed or not available on this system."
    except subprocess.TimeoutExpired:
        return "Git diff command timed out."


@tool(description="Index the most recent git commits into the project knowledge base. Provide 'n_commits' (default 20). Call this first before searching commit history.")
def index_commits(n_commits: int = 20) -> str:
    count = commit_history_service.index_commits(n_commits)
    return f"Indexed {count} commits into project history."


@tool(description="Search the indexed commit history for relevant commits. Provide a 'query' describing what you're looking for — e.g., 'when was retry logic added', 'middleware changes'.")
def search_history(query: str) -> str:
    return commit_history_service.search_history(query)


@tool(description="Search technical documentation (Python, Git, LangChain, code review) for relevant information. Provide a 'query' describing what you want to find.")
def doc_search(query: str) -> str:
    return rag.rag_summarize(query)
