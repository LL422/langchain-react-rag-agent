<div align="center">

# gitwise — AI-Powered Git History Intelligence

**Turn every commit into searchable project memory. A ReAct Agent that indexes git history, answers "why was this code written this way?", and traces decisions back to their source.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.x-green?logo=langchain)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.x-orange)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red?logo=streamlit)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

</div>

---

## What is gitwise?

`gitwise` is a CLI tool that makes your project's entire commit history **semantically searchable**. After indexing, you can ask questions like _"How did the middleware system evolve?"_ or _"When and why was retry logic added?"_ — and the Agent autonomously searches commits, reads relevant files, and traces the full story.

> **It's not a chatbot. It's not a code reviewer. It's your project's long-term memory.**

---

## Demo

```bash
$ python devbot.py index
  Indexed 2 commits into project memory.

$ python devbot.py
  1. PR Review
  2. Code Audit
  3. Docs Generator
  4. Interactive Chat
  5. Project Memory    ← ask "why" questions about your codebase
  0. Exit

  Choice [0-5]: 5
  → How did the middleware system evolve in this project?
```

```
  Commit    Date            Description
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  c411202   May 19, 01:38   Initial build: ReAct Agent + RAG
  2a07284   May 19, 22:22   Pivot to DevBot with project memory

  Key Decision: Dynamic Prompt Switching

  agent/tools/middleware.py:12-28 — The @dynamic_prompt middleware
  switches between "general assistant" and "code reviewer" personas
  based on keywords detected in doc_search queries. When a user asks
  about "security" or "review", the runtime context flips to review
  mode and loads a different system prompt for the next model call.
```

---

## Architecture

```
User Input (CLI or Streamlit)
      │
      ▼
┌─────────────────────────────────────────┐
│            ReAct Agent                   │
│                                          │
│  ┌──────────┐    ┌──────────────────┐   │
│  │ Thought  │───→│     Action       │   │
│  │(Reasoning)│   │(Tool Call / RAG) │   │
│  └──────────┘    └────────┬─────────┘   │
│       ↑                   │              │
│       └─── Observation ◄──┘              │
│                                          │
│   Middleware: Tool Monitoring · Dynamic  │
│              Prompt Switching           │
└─────────────────────────────────────────┘
      │                │              │
      ▼                ▼              ▼
┌──────────┐   ┌────────────┐  ┌──────────┐
│ Chroma   │   │  Developer │  │ Dynamic  │
│ Vector   │   │   Tools    │  │ Prompt   │
│ Store    │   │            │  │ Switch   │
└──────────┘   └────────────┘  └──────────┘
```

### Tools

| Tool | Description |
|------|-------------|
| `search_codebase` | Full-text search (ripgrep) with context and file filtering |
| `read_file` | Read files with line-range control, path-scoped to project |
| `list_directory` | Navigate project structure with file sizes |
| `git_history` | Recent commit history in one-line format |
| `git_diff` | Diff between branches, commits, or working tree |
| `index_commits` | Index git commits into Chroma vector store |
| `search_history` | Semantic search over indexed commit history |
| `doc_search` | RAG lookup over programming best practices |

### Middleware

| Middleware | Type | Purpose |
|------------|------|---------|
| `monitor_tool` | `@wrap_tool_call` | Logs every tool call and detects code review intent |
| `log_before_model` | `@before_model` | Logs agent state before each LLM invocation |
| `review_prompt_switch` | `@dynamic_prompt` | Switches system prompt to code reviewer persona |

---

## Quick Start

### Requirements

- **Python** >= 3.10
- **LM Studio** with an embedding model loaded (for Chroma vector store)
- A chat model provider (DeepSeek, OpenAI, or local)

### 1. Clone

```bash
git clone https://github.com/LL422/gitwise.git
cd gitwise
```

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Configure

Copy `.env.example` to `.env` and fill in your credentials:

```bash
# Chat model — any OpenAI-compatible API
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-your-api-key

# Embedding model — local LM Studio (default)
EMBED_BASE_URL=http://localhost:1234/v1
EMBED_API_KEY=not-needed
```

> **Embedding**: Start LM Studio, load `text-embedding-bge-small-en-v1.5`, and start the Local Server on port `1234`.

### 4. Initialize

```bash
# Load the knowledge base into Chroma (first run only)
python -c "from rag.vector_store import VectorStoreService; VectorStoreService().load_document()"

# Index your git history
python devbot.py index
```

### 5. Run

```bash
python devbot.py          # Interactive menu
python devbot.py index    # Index commits (skip menu)
python devbot.py --project /path/to/other/repo   # Analyze another project
streamlit run app.py      # Web chat interface
```

---

## Project Structure

```
gitwise/
│
├── agent/                          # Agent Layer
│   ├── react_agent.py              #   ReAct Agent with streaming + conversation memory
│   └── tools/
│       ├── agent_tools.py          #   8 tools (search, read, git, RAG, history)
│       └── middleware.py           #   Monitoring, logging, dynamic prompt switching
│
├── rag/                            # RAG Pipeline
│   ├── vector_store.py             #   Chroma vector store with MD5 deduplication
│   ├── rag_service.py              #   Retrieval → LLM summarization
│   └── commit_history.py           #   Commit indexing into Chroma (Project Memory)
│
├── model/
│   └── factory.py                  #   Abstract factory for swappable LLM + embedding providers
│
├── config/                         # YAML Configuration
│   ├── agent.yml                   #   Agent behavior settings
│   ├── chroma.yml                  #   Vector store parameters (chunk size, Top-K, etc.)
│   ├── prompts.yml                 #   Prompt template paths
│   └── rag.yml                     #   Model names
│
├── prompts/                        # Prompt Templates
│   ├── main_prompt.txt             #   Default developer assistant persona
│   ├── code_review_prompt.txt      #   Code reviewer persona (dynamic switch)
│   ├── trace.txt                   #   Decision trace mode (Project Memory)
│   ├── task_review.txt             #   PR Review task pipeline
│   ├── task_audit.txt              #   Code Audit task pipeline
│   ├── task_docs.txt               #   Architecture Docs task pipeline
│   └── rag_summarize.txt           #   RAG summarization instructions
│
├── data/                           # Knowledge Base
│   ├── python_best_practices.txt
│   ├── git_reference.txt
│   ├── langchain_guide.txt
│   └── code_review_checklist.txt
│
├── utils/                          # Utilities
│   ├── config_handler.py           #   YAML config loader
│   ├── file_handler.py             #   PDF/TXT parsing
│   ├── logger_handler.py           #   Structured logging
│   ├── path_tool.py                #   Absolute path resolution
│   └── prompt_loader.py            #   Prompt file loading
│
├── devbot.py                       # CLI entry point
├── app.py                          # Streamlit web UI
├── requirements.txt
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Agent** | LangChain + LangGraph (ReAct loop, create_agent) |
| **LLM** | ChatOpenAI → DeepSeek / OpenAI / LM Studio / DashScope |
| **Embedding** | Local BGE/Nomic via LM Studio (OpenAI-compatible) |
| **Vector Store** | Chroma (persistent, local) |
| **Frontend** | Streamlit (streaming) + Rich (terminal) |
| **Config** | YAML-driven with environment variable overrides |

---

## Modes

| Mode | What it does | How to run |
|------|-------------|------------|
| **Project Memory** | Trace decisions, explain code evolution, answer "why" questions | `python devbot.py` → 5 |
| **PR Review** | Review git changes between branches/commits | `python devbot.py` → 1 |
| **Code Audit** | Audit a directory for security/performance/readability/correctness | `python devbot.py` → 2 |
| **Docs Generator** | Generate architecture documentation | `python devbot.py` → 3 |
| **Interactive Chat** | Multi-turn conversation with history | `python devbot.py` → 4 |

---

## License

This project is licensed under the [MIT License](./LICENSE).
