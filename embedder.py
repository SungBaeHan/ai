from sentence_transformers import SentenceTransformer
_model = None
def get_embedder():
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-m3")
    return _model
def embed(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    return model.encode(texts, normalize_embeddings=True).tolist()
