from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-mpnet-base-v2")

def generate_embeddings(text):
    return model.encode(text)
