from typing import Callable
from utils.prompt_loader import load_system_prompts, load_report_prompts
from langchain.agents import AgentState
from langchain.agents.middleware import wrap_tool_call, before_model, dynamic_prompt, ModelRequest
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.runtime import Runtime
from langgraph.types import Command
from utils.logger_handler import logger


@wrap_tool_call
def monitor_tool(
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    logger.info(f"[tool monitor] Executing tool: {request.tool_call['name']}")
    logger.info(f"[tool monitor] Arguments: {request.tool_call['args']}")

    try:
        result = handler(request)
        logger.info(f"[tool monitor] Tool {request.tool_call['name']} succeeded")

        if request.tool_call['name'] == "doc_search":
            query = request.tool_call['args'].get("query", "")
            review_keywords = ["review", "security", "performance", "code review",
                             "readability", "best practice", "anti-pattern", "vulnerability"]
            if any(kw in query.lower() for kw in review_keywords):
                request.runtime.context["review"] = True

        return result
    except Exception as e:
        logger.error(f"Tool {request.tool_call['name']} failed: {str(e)}")
        raise e


@before_model
def log_before_model(
        state: AgentState,
        runtime: Runtime,
):
    logger.info(f"[log_before_model] About to invoke model with {len(state['messages'])} messages")
    last_msg = state['messages'][-1]
    content = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
    logger.debug(f"[log_before_model] {type(last_msg).__name__} | {str(content)[:200]}")
    return None


@dynamic_prompt
def review_prompt_switch(request: ModelRequest):
    is_review = request.runtime.context.get("review", False)
    if is_review:
        return load_report_prompts()
    return load_system_prompts()
