import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
import streamlit as st
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

st.set_page_config(page_title="LLM Demo App", layout="wide")
st.title("LLM Demo app with tooling")

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}
st.session_state.current_model = 'gemini-1.5-flash-8b'
if "messages" not in st.session_state:
    st.session_state.messages = []
# if "current_mode" not in st.session_state:
#     st.session_state.current_mode = "chat"  # "chat" or "compare"
if "comparison_results" not in st.session_state:
    st.session_state.comparison_results = []
if "use_search_tool" not in st.session_state:
    st.session_state.use_search_tool = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.sidebar:
  st.header("Configuration")
  
  st.session_state.use_search_tool = st.toggle("Enable web search capabilities", value=st.session_state.use_search_tool)
  if st.session_state.use_search_tool:
    model = genai.GenerativeModel(
      model_name="gemini-1.5-flash-8b",
      generation_config=generation_config,
      tools = [
        genai.protos.Tool(
          google_search_retrieval = genai.protos.GoogleSearchRetrieval(
            dynamic_retrieval_config = genai.protos.DynamicRetrievalConfig(
              mode = genai.protos.DynamicRetrievalConfig.Mode.MODE_DYNAMIC,
              dynamic_threshold = 0.3,
            ),
          ),
        ),
      ],
    )
  else:
    model = genai.GenerativeModel(
      model_name="gemini-1.5-flash-8b",
      generation_config=generation_config,
    )

  if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.comparison_results = []
        st.session_state.chat_history = []
        st.rerun()
  system_prompt = st.sidebar.text_input(f"Prompt", type="default")
  if system_prompt:
    model = genai.GenerativeModel(
          model_name="gemini-1.5-flash-8b",
          generation_config=generation_config,
          system_instruction=system_prompt+"make the appropriate assumptions",
    )


chat_session = model.start_chat()

# Chat input
user_input = st.chat_input("Type your message here...")

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
      st.write(message["content"])
      if "timestamp" in message:
          st.caption(f"Sent: {message['timestamp']} | Model: {message['model']}")

if user_input:
        # Add user message to chat history
        st.session_state.messages.append({
            "role": "user", 
            "content": user_input,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": "User"
        })
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Validate API key
          # Show assistant thinking
        with st.chat_message("assistant"):
            with st.spinner(f"Thinking using ..."):
                response = model.generate_content(user_input)
                st.write(response.text)
            
            # Add assistant response to chat history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response.text,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model": f"{st.session_state.current_model}{' with web search' if st.session_state.use_search_tool else ''}"
            })
