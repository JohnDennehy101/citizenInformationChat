import logging
import numpy as np
from transformers import AutoTokenizer, AutoModel
logger = logging.getLogger(__name__)

class ModelService:
    # TODO: Add error handling for this file
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def get_embedding(self, text):
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, padding=True)
        outputs = self.model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1).detach().numpy()
        return embeddings[0]

    def chunk_text(self, text, max_length=1024):
        tokens = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=max_length, padding=True)
        chunks = []
        for i in range(0, len(tokens['input_ids'][0]), max_length):
            chunk = self.tokenizer.decode(tokens['input_ids'][0][i:i+max_length], skip_special_tokens=True)
            chunks.append(chunk)
        return chunks