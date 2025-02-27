import faiss

from utils.index import FAISSIndex
from utils.oai import OAIEmbedding


def find_context(question: str, index_path: str):
    index = FAISSIndex(index=faiss.IndexFlatL2(1536), embedding=OAIEmbedding())
    index.load(path=index_path)
    snippets = index.query(question, top_k=5)
    return snippets
