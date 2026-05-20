"""
Commit History Knowledge Base — indexes git commits into Chroma for semantic search.
"""
import subprocess
from langchain_chroma import Chroma
from langchain_core.documents import Document
from model.factory import embed_model
from utils.config_handler import chroma_conf
from utils.path_tool import get_project_root
from utils.logger_handler import logger
import os


class CommitHistoryService:
    """Stores and searches git commit history using Chroma vector store."""

    COLLECTION_NAME = "commit_history"

    def __init__(self):
        persist_dir = chroma_conf.get("persist_directory", "chroma_db")
        self.vector_store = Chroma(
            collection_name=self.COLLECTION_NAME,
            embedding_function=embed_model,
            persist_directory=persist_dir,
        )
        self.project_root = get_project_root()

    def index_commits(self, n: int = 20) -> int:
        """
        Index the last N commits into the vector store.
        Returns the number of commits indexed.
        """
        logs = self._get_commit_logs(n)
        if not logs:
            logger.warning("[commit_history] No commits found")
            return 0

        documents: list[Document] = []
        for entry in logs:
            hash_short = entry["hash"]
            diff_text = self._get_commit_diff(hash_short)
            content = (
                f"Commit: {hash_short}\n"
                f"Date: {entry['date']}\n"
                f"Message: {entry['message']}\n\n"
                f"Diff:\n{diff_text}"
            )
            documents.append(Document(
                page_content=content,
                metadata={
                    "hash": hash_short,
                    "date": entry["date"],
                    "message": entry["message"],
                    "source": "git",
                },
            ))

        self.vector_store.add_documents(documents)
        logger.info(f"[commit_history] Indexed {len(documents)} commits")
        return len(documents)

    def search_history(self, query: str, k: int = 5) -> str:
        """Search indexed commit history for relevant commits."""
        retriever = self.vector_store.as_retriever(search_kwargs={"k": k})
        docs = retriever.invoke(query)
        if not docs:
            return "No relevant commits found in project history."
        results = []
        for i, doc in enumerate(docs, 1):
            md = doc.metadata
            results.append(
                f"[Commit {i}] {md.get('hash', '?')} | {md.get('date', '?')}\n"
                f"  {md.get('message', 'no message')}\n"
                f"  Content: {doc.page_content[:500]}..."
            )
        return "\n\n".join(results)

    def _get_commit_logs(self, n: int) -> list[dict]:
        try:
            result = subprocess.run(
                ["git", "log", f"-n{n}", "--format=%h|%ad|%s", "--date=short"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=self.project_root, timeout=15,
            )
            output = result.stdout.strip()
            if not output:
                return []
            entries = []
            for line in output.split("\n"):
                parts = line.split("|", 2)
                if len(parts) == 3:
                    entries.append({
                        "hash": parts[0],
                        "date": parts[1],
                        "message": parts[2],
                    })
            return entries
        except Exception as e:
            logger.error(f"[commit_history] Failed to get git log: {e}")
            return []

    def _get_commit_diff(self, commit_hash: str) -> str:
        try:
            result = subprocess.run(
                ["git", "show", "--stat", "--patch", commit_hash],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                cwd=self.project_root, timeout=20,
            )
            output = result.stdout.strip()
            max_chars = 2500
            if len(output) > max_chars:
                output = output[:max_chars] + "\n... (truncated)"
            return output
        except Exception as e:
            logger.error(f"[commit_history] Failed to get diff for {commit_hash}: {e}")
            return "(diff unavailable)"


# Module-level singleton
commit_history_service = CommitHistoryService()
