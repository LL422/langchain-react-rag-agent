<div align="center">

# DevBot · Developer Assistant

**A developer productivity agent powered by LangChain ReAct Agent + RAG, running on local LLMs via LM Studio**

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
&nbsp;
[![LangChain](https://img.shields.io/badge/LangChain-1.x-green)](https://www.langchain.com/)
&nbsp;
[![LangGraph](https://img.shields.io/badge/LangGraph-1.x-orange)](https://github.com/langchain-ai/langgraph)
&nbsp;
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)](https://streamlit.io/)
&nbsp;
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

</div>

---

## Overview

**DevBot** is a ReAct (Reasoning + Acting) Agent that acts as an AI pair programmer. It can search your codebase, read files, analyze git history, and retrieve technical documentation — all through natural language conversation. Built on LangChain + LangGraph, with a RAG-powered knowledge base and dynamic prompt switching between general assistance and code review modes.

## Features

| Feature | Description |
|---|---|
| **Codebase Search** | Full-text search across the project using ripgrep with context display |
| **File Reading** | Read any file with line-range control, path-scoped to project root |
| **Git History** | Query recent commits to understand changes and evolution |
| **Directory Navigation** | List project structure at any level of the tree |
| **RAG Doc Lookup** | Retrieve Python best practices, Git reference, LangChain guide, and code review checklist |
| **Dynamic Prompt Switching** | Automatically switches to code review persona when analyzing code quality |
| **Streaming UI** | Streamlit-powered, real-time reasoning and tool execution visualization |
| **Local LLM** | Runs entirely offline with LM Studio — no cloud API keys needed |

## Architecture

```
User Input (Streamlit)
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
│   RAG    │   │ Developer  │  │  Prompt  │
│  Chroma  │   │   Tools    │  │ Dynamic  │
│  Vector  │   │            │  │ Switch   │
│  Store   │   │            │  │ Manager  │
└──────────┘   └────────────┘  └──────────┘
```

### Tools

| Tool | Description |
|---|---|
| `search_codebase` | grep/ripgrep across project files with context |
| `read_file` | Read file contents with optional line range |
| `list_directory` | List directory contents with file sizes |
| `git_history` | Show recent git commits |
| `doc_search` | RAG lookup over technical documentation |

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Local Qwen models via LM Studio (OpenAI-compatible API) |
| Agent Framework | LangChain + LangGraph |
| Vector Database | Chroma |
| Embedding | BGE / Nomic Embed (local via LM Studio) |
| Frontend | Streamlit |
| Configuration | YAML-driven |

## Quick Start

### Requirements

- **Python** >= 3.10
- **LM Studio** with a chat model and an embedding model loaded

### 1. Clone

```bash
git clone https://github.com/LL422/langchain-react-rag-agent.git
cd langchain-react-rag-agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure LM Studio

- Download and install [LM Studio](https://lmstudio.ai/)
- Load a chat model (e.g., `qwen2.5-7b-instruct`) and an embedding model (e.g., `text-embedding-bge-small-en-v1.5`)
- Start the Local Server (default port `1234`)
- Update model names in `config/rag.yml` if using different models

### 4. Initialize the Knowledge Base

```bash
python -c "from rag.vector_store import VectorStoreService; VectorStoreService().load_document()"
```

### 5. Launch

```bash
streamlit run app.py
```

### Test Queries

Try these after launching:

- *What design patterns are used in this project?* — codebase analysis
- *Search the codebase for all uses of create_agent* — code search
- *Show me the recent git history* — git log
- *Review agent/tools/middleware.py for potential issues* — code review mode
- *What does the LangChain guide say about tool error handling?* — RAG doc lookup

## Project Structure

```
langchain-react-rag-agent/
│
├── agent/                          # Agent Core
│   ├── react_agent.py              #   ReAct Agent main logic
│   └── tools/
│       ├── agent_tools.py          #   5 developer tools
│       └── middleware.py           #   Tool monitoring + dynamic prompt switching
│
├── rag/                            # RAG Pipeline
│   ├── vector_store.py             #   Chroma vector store · MD5 dedup
│   └── rag_service.py              #   Retrieval → LLM summarization
│
├── model/
│   └── factory.py                  # Model factory (ChatOpenAI + custom embeddings)
│
├── config/                         # YAML Configuration
│   ├── agent.yml
│   ├── chroma.yml
│   ├── prompts.yml
│   └── rag.yml
│
├── prompts/                        # Prompt Templates
│   ├── main_prompt.txt             #   Developer assistant system prompt
│   ├── code_review_prompt.txt      #   Code reviewer persona
│   └── rag_summarize.txt           #   RAG summarization prompt
│
├── data/                           # Knowledge base (programming docs)
│   ├── python_best_practices.txt
│   ├── git_reference.txt
│   ├── langchain_guide.txt
│   └── code_review_checklist.txt
│
├── utils/                          # Utilities
│   ├── config_handler.py
│   ├── file_handler.py
│   ├── logger_handler.py
│   ├── path_tool.py
│   └── prompt_loader.py
│
├── app.py                          # Streamlit entry point
├── requirements.txt
└── README.md
```

## Configuration

| File | Description |
|---|---|
| `rag.yml` | Chat and embedding model names |
| `chroma.yml` | Chroma persistence, chunk size, Top-K, allowed file types |
| `prompts.yml` | Paths to prompt templates |
| `agent.yml` | Agent-level settings |

## License

This project is licensed under the [MIT License](./LICENSE).
