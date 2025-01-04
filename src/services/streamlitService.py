import logging
import ollama
import streamlit as st
import numpy as np
from streamlit_chat import message
from ragas import evaluate, EvaluationDataset
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
    
    def evaluate_response(self, query, response, relevant_texts):
        retrieved_documents = [row[0] for row in relevant_texts]

        response_text = response["message"]["content"] if isinstance(response, dict) else response

        # Hardcoding for reference - query was "Rental tax credit"
        # Will have to make this dynamic going forward for evaluation
        ground_truth = "Rental tax credit is extended to parents of students renting a room or digs in 2024. The tax credit will also be available to claim for the 2022 and 2023 tax years."

        ragas_input = [{
            "query": query,
            "ground_truth": ground_truth,
            "answer": ground_truth,
            "contexts": retrieved_documents,
            "response": response_text,
            "retrieved_contexts": retrieved_documents,
            "reference": response_text,
            "user_input": query
        }]

        evaluation_dataset = EvaluationDataset.from_list(ragas_input)

        evaluation_results = evaluate(evaluation_dataset, raise_exceptions=True)

        return evaluation_results

    def process_input(self):
        if st.session_state["user_input"] and len(st.session_state["user_input"].strip()) > 0:
            user_text = st.session_state["user_input"].strip()
            with st.session_state["thinking_spinner"], st.spinner(f"Thinking"):
                relevant_texts = self.fetch_relevant_texts(user_text)
                agent_text = self.generate_response(user_text, relevant_texts)

                # COMMENTING OUT FOR NOW - THIS WORKS BUT USAGE COSTS DUE TO RAGAS USING OPEN AI API
                # Use in combination with manual evaluation metrics
                #evaluation = self.evaluate_response(user_text, agent_text, relevant_texts)

                #print(evaluation)

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
