import logging
import ollama
import streamlit as st
import numpy as np
from streamlit_chat import message
logger = logging.getLogger(__name__)

class StreamlitService:
    # TODO: Add error handling for this file
    def __init__(self, dbConnection, modelService):
        self.dbConnection = dbConnection
        self.modelService = modelService

    def fetch_relevant_texts(self, query, top_k=5):
        query_embedding = self.modelService.get_embedding(query)

        query_embedding_str = np.array(query_embedding)
        sql_query = """
            SELECT text, embedding, (embedding <=> %s) AS distance
            FROM text_embeddings
            ORDER BY distance ASC
            LIMIT %s;
        """
        with self.dbConnection.cursor() as cursor:
            cursor.execute(sql_query, (query_embedding_str, top_k))
            results = cursor.fetchall()
            return results
    
    def generate_response(self, query, relevant_texts):
        SYS_PROMPT = """You are an assistant for answering questions.
        You are given the extracted parts of a long document and a question. Provide a conversational answer.
        If you don't know the answer, just say "I do not know." Don't make up an answer."""
    
        PROMPT = f"Question:{query}\nContext:"
        for text, _, _ in relevant_texts:
            PROMPT+= f"{text}\n"

        messages = [{"role":"system","content":SYS_PROMPT},{"role":"user","content":PROMPT}]
        output = ollama.chat(
        model = "llama3.1",
        messages = messages,
        )

        return output

    def process_input(self):
        if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
            user_text = st.session_state["user_input"].strip()
            with st.session_state["thinking_spinner"], st.spinner(f"Thinking"):
                relevant_texts = self.fetch_relevant_texts(user_text)
                agent_text = self.generate_response(user_text, relevant_texts)
            st.session_state["messages"].append((user_text, True))
            st.session_state["messages"].append((agent_text['message']['content'], False))
    
    def display_messages(self):
        st.subheader("Citizen Information Chat")
        for i, (msg, is_user) in enumerate(st.session_state["messages"]):
            message(msg, is_user=is_user, key=str(i))
        st.session_state["thinking_spinner"] = st.empty()

    def render_user_interface(self):
        try:
            if len(st.session_state) == 0:
                st.session_state["messages"] = []

            st.session_state["ingestion_spinner"] = st.empty()

            self.display_messages()
            st.text_input("Message", key="user_input", on_change=self.process_input)
        except Exception as e:
            logger.info(e)
