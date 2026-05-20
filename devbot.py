"""
DevBot CLI — Developer Task Pipeline
Usage: python devbot.py [--project PATH]
"""
import os
import sys
import argparse
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

from agent.react_agent import ReactAgent
from agent.tools.agent_tools import set_project_root, get_current_project_root
from utils.path_tool import get_project_root
from utils.logger_handler import logger

console = Console()

REPORTS_DIR = os.path.join(get_project_root(), "reports")

TASK_PROMPTS = {
    "1": {
        "name": "PR Review",
        "prompt_file": "prompts/task_review.txt",
        "param_name": "git target",
        "param_help": "e.g., main..feature-branch, HEAD~3..HEAD",
        "param_key": "target",
        "file_prefix": "review",
    },
    "2": {
        "name": "Code Audit",
        "prompt_file": "prompts/task_audit.txt",
        "param_name": "directory path",
        "param_help": "e.g., agent/, rag/, src/",
        "param_key": "target",
        "file_prefix": "audit",
    },
    "3": {
        "name": "Docs Generator",
        "prompt_file": "prompts/task_docs.txt",
        "param_name": "project name",
        "param_help": "e.g., DevBot",
        "param_key": "project_name",
        "file_prefix": "architecture",
    },
    "5": {
        "name": "Project Memory",
        "prompt_file": "prompts/trace.txt",
        "param_name": "question",
        "param_help": "e.g., How did the middleware system evolve?",
        "param_key": "query",
        "file_prefix": "trace",
    },
}


def check_env() -> bool:
    """Verify essential configuration."""
    missing = []
    if not os.getenv("LLM_API_KEY") or os.getenv("LLM_API_KEY") == "sk-placeholder":
        missing.append("LLM_API_KEY")
    if missing:
        console.print()
        console.print(Panel.fit(
            "[bold red]Missing Configuration[/]\n\n"
            "Set the following in your [cyan].env[/] file:\n"
            f"  [yellow]{' '.join(missing)}[/]\n\n"
            "Copy [cyan].env.example[/] → [cyan].env[/] and fill in your API key.",
            border_style="red",
        ))
        return False
    return True


def load_prompt(filepath: str, replacements: dict[str, str]) -> str:
    path = os.path.join(get_project_root(), filepath)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for key, value in replacements.items():
        content = content.replace(f"{{{key}}}", value)
    return content


def run_task(choice: str, param_value: str) -> str | None:
    task = TASK_PROMPTS[choice]
    replacements = {task["param_key"]: param_value}
    system_prompt = load_prompt(task["prompt_file"], replacements)
    user_query = f"Execute the full task pipeline for: {param_value}"

    console.print()
    console.print(Panel(
        f"[bold white]{task['name']}[/]\n"
        f"[dim]Target: {param_value}[/]",
        border_style="cyan",
    ))

    agent = ReactAgent(system_prompt=system_prompt)

    collected: list[str] = []
    tool_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task_id = progress.add_task("[cyan]Analyzing...", total=None)

        for chunk in agent.execute_stream(user_query):
            text = chunk.strip()
            if not text:
                continue

            # Detect tool calls by monitoring middleware patterns in output
            if text.startswith("[tool monitor]") or text.startswith("[log_before_model]"):
                continue

            # Show tool results as brief updates
            if any(text.startswith(kw) for kw in ["Changed files", "  [DIR]", "  [FILE]", "Recent ", "No matches", "No commits", "No changes"]):
                progress.update(task_id, description=f"[dim]{text.split(chr(10))[0][:80]}[/]")

            collected.append(chunk)

    console.print()

    full = "".join(collected)
    if not full.strip():
        console.print("[yellow]No output generated.[/]")
        return None

    # Render the report as markdown in terminal
    try:
        md = Markdown(full)
        console.print(md)
    except Exception:
        console.print(full)

    return full


def save_report(content: str, prefix: str, target: str) -> str:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_target = target.replace("..", "_").replace("/", "_").replace("\\", "_")
    # Remove Windows-invalid filename characters
    for char in '<>:"|?*':
        safe_target = safe_target.replace(char, "")
    safe_target = safe_target.strip("._ ")
    filename = f"{prefix}_{safe_target}_{timestamp}.md"
    filepath = os.path.join(REPORTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def show_header(project_path: str):
    console.print()
    console.print(Panel(
        "[bold cyan]DevBot[/] - Developer Task Pipeline\n"
        f"[dim]Project: {project_path}[/]",
        border_style="cyan",
    ))


def show_menu():
    console.print("  [bold cyan]1.[/] PR Review        - Review git changes between branches/commits")
    console.print("  [bold cyan]2.[/] Code Audit       - Audit a directory for code quality")
    console.print("  [bold cyan]3.[/] Docs Generator   - Generate architecture documentation")
    console.print("  [bold cyan]4.[/] Interactive Chat - Multi-turn conversation with history")
    console.print("  [bold cyan]5.[/] Project Memory   - Trace decisions and code evolution")
    console.print("  [bold cyan]0.[/] Exit")
    console.print()
    console.print()


def interactive_chat(agent: ReactAgent):
    console.print()
    console.print(Panel(
        "[bold]Interactive Chat Mode[/]\n"
        "[dim]Type your questions. Use /clear to reset history. /exit to quit.[/]",
        border_style="green",
    ))
    console.print()

    while True:
        try:
            query = console.input("[bold green]You ›[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n")
            break

        if not query:
            continue
        if query.lower() == "/exit":
            break
        if query.lower() == "/clear":
            agent.clear_history()
            console.print("  [dim]History cleared.[/]")
            continue

        console.print()
        response = agent.chat(query)

        try:
            console.print(Markdown(response))
        except Exception:
            console.print(response)
        console.print()


def run_index_command(n_commits: int):
    """Index commits without going through the menu."""
    from rag.commit_history import commit_history_service
    console.print()
    console.print("  [cyan]Indexing commits...[/]")
    count = commit_history_service.index_commits(n_commits)
    if count > 0:
        console.print(f"  [bold green]Indexed {count} commits into project memory.[/]\n")
    else:
        console.print("  [yellow]No commits indexed.[/]\n")


def main():
    parser = argparse.ArgumentParser(description="DevBot — Developer Task Pipeline")
    parser.add_argument("--project", "-p", type=str, default=None,
                       help="Path to the project to analyze (default: DevBot itself)")
    parser.add_argument("command", nargs="?", default=None,
                       choices=[None, "index"],
                       help="Run directly: 'index' to index commits")
    parser.add_argument("--all", action="store_true",
                       help="Index all commits (for 'index' command)")
    args = parser.parse_args()

    # Set project root
    if args.project:
        target_path = os.path.abspath(args.project)
        if not os.path.isdir(target_path):
            console.print(f"[red]Project path not found: {args.project}[/]")
            sys.exit(1)
        set_project_root(target_path)
    else:
        target_path = get_project_root()

    # Handle direct commands
    if args.command == "index":
        n = 0 if args.all else 30
        show_header(target_path)
        run_index_command(n)
        return

    show_header(target_path)

    if not check_env():
        sys.exit(1)

    # Verify it's a git repo for git-based tools
    git_dir = os.path.join(target_path, ".git")
    if not os.path.isdir(git_dir):
        console.print("[yellow]Note:[/] Not a git repository — git tools will be unavailable.\n")

    show_menu()

    while True:
        try:
            choice = console.input("[bold cyan]Choice[/] [0-5]: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n")
            break

        if choice == "0":
            console.print("  Goodbye.\n")
            break
        elif choice == "4":
            agent = ReactAgent()
            interactive_chat(agent)
            show_menu()
            continue
        elif choice in TASK_PROMPTS:
            task = TASK_PROMPTS[choice]
            console.print(f"  [dim]{task['param_name']} ({task['param_help']})[/]")
            param = console.input(f"  [bold cyan]→[/] ").strip()
            if not param:
                console.print("  [red]Parameter required.[/]")
                continue

            content = run_task(choice, param)

            if content and content.strip():
                filepath = save_report(content, task["file_prefix"], param)
                console.print(f"\n[bold green]Report saved:[/] [cyan]{filepath}[/]\n")
            break
        else:
            console.print("  [red]Invalid choice. Enter 0-5.[/]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n  [dim]Cancelled.[/]\n")
    except Exception as e:
        logger.error(f"DevBot crashed: {str(e)}", exc_info=True)
        console.print(f"\n[red]Error: {e}[/]\n")
        sys.exit(1)
