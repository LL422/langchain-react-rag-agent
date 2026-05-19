import streamlit as st
from agent.react_agent import ReactAgent

st.set_page_config(page_title="SmartClean AI · Customer Support", page_icon="🤖")
st.title("🤖 SmartClean Robotic Vacuum Support")
st.caption("Powered by LangChain ReAct Agent + RAG Retrieval-Augmented Generation")
st.divider()

if "agent" not in st.session_state:
    st.session_state["agent"] = ReactAgent()

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for message in st.session_state["messages"]:
    st.chat_message(message["role"]).write(message["content"])

prompt = st.chat_input()

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["messages"].append({"role": "user", "content": prompt})

    response_messages: list[str] = []
    with st.spinner("Thinking..."):
        res_stream = st.session_state["agent"].execute_stream(prompt)

        def stream_generator(generator, cache_list):
            """Stream output character by character while caching the full response."""
            for chunk in generator:
                cache_list.append(chunk)
                for char in chunk:
                    yield char

        st.chat_message("assistant").write_stream(stream_generator(res_stream, response_messages))
        st.session_state["messages"].append({"role": "assistant", "content": "".join(response_messages)})
        st.rerun()
