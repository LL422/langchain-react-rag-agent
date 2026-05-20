from langchain.agents import create_agent
from model.factory import chat_model
from utils.prompt_loader import load_system_prompts
from agent.tools.agent_tools import (search_codebase, read_file, list_directory,
                                     git_history, git_diff, doc_search,
                                     index_commits, search_history)
from agent.tools.middleware import monitor_tool, log_before_model, review_prompt_switch


class ReactAgent:
    """ReAct Agent with conversation memory and optional project root override."""

    def __init__(self, system_prompt: str | None = None):
        if system_prompt is None:
            system_prompt = load_system_prompts()
        self.system_prompt = system_prompt
        self.agent = create_agent(
            model=chat_model,
            system_prompt=self.system_prompt,
            tools=[search_codebase, read_file, list_directory, git_history, git_diff, doc_search,
           index_commits, search_history],
            middleware=[monitor_tool, log_before_model, review_prompt_switch],
        )
        self.history: list[dict] = []

    def execute_stream(self, query: str, history: list[dict] | None = None):
        """Stream agent response. Use history for multi-turn context."""
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": query})

        input_dict = {"messages": messages}

        for chunk in self.agent.stream(input_dict, stream_mode="values", context={"review": False}):
            latest_message = chunk["messages"][-1]
            if latest_message.content:
                yield latest_message.content.strip() + "\n"

    def execute_full(self, query: str) -> str:
        """Execute query and return the complete response as a single string."""
        parts: list[str] = []
        for chunk in self.execute_stream(query):
            parts.append(chunk)
        return "".join(parts)

    def chat(self, query: str) -> str:
        """Send a message and get the full response. Maintains conversation history."""
        response = self.execute_full_with_history(query)
        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": response})
        # Keep history bounded to prevent context overflow
        if len(self.history) > 20:
            self.history = self.history[-20:]
        return response

    def execute_full_with_history(self, query: str) -> str:
        """Like execute_full but uses self.history for context."""
        parts: list[str] = []
        for chunk in self.execute_stream(query, history=self.history):
            parts.append(chunk)
        return "".join(parts)

    def clear_history(self):
        self.history = []


if __name__ == '__main__':
    agent = ReactAgent()
    for chunk in agent.execute_stream("What design patterns does this project use?"):
        print(chunk, end="", flush=True)
