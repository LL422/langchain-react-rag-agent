import streamlit as st
from agent.react_agent import ReactAgent

st.set_page_config(page_title="DevBot · Developer Assistant", page_icon="💻")
st.title("💻 DevBot · Developer Assistant")
st.caption("Powered by LangChain ReAct Agent + RAG — Code Search, Git Analysis & Doc Lookup")
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

    response_messages: list[str] = []
    with st.spinner("Analyzing..."):
        # Pass conversation history for multi-turn context
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state["messages"]
        ]
        res_stream = st.session_state["agent"].execute_stream(prompt, history=history)

        def stream_generator(generator, cache_list):
            for chunk in generator:
                cache_list.append(chunk)
                for char in chunk:
                    yield char

        st.chat_message("assistant").write_stream(stream_generator(res_stream, response_messages))

    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.session_state["messages"].append({"role": "assistant", "content": "".join(response_messages)})
    st.rerun()
