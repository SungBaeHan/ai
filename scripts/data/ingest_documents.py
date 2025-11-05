import os, glob
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from pypdf import PdfReader
from adapters.external.embedding.sentence_transformer import embed
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = os.getenv("COLLECTION", "my_docs")
def read_docs(folder: str):
    texts=[]
    for path in glob.glob(os.path.join(folder, "**/*"), recursive=True):
        low=path.lower()
        try:
            if low.endswith(".pdf"):
                txt="\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
            elif low.endswith((".txt",".md")):
                txt=open(path,"r",encoding="utf-8",errors="ignore").read()
            else: continue
            if txt.strip(): texts.append((path, txt))
        except Exception: pass
    return texts
def chunk(t,size=700,overlap=120):
    out=[]; i=0
    while i < len(t): out.append(t[i:i+size]); i += size-overlap
    return out
def main(folder: str):
    cli=QdrantClient(url=QDRANT_URL)
    try:
        cli.create_collection(COLLECTION, vectors_config=qm.VectorParams(size=1024, distance=qm.Distance.COSINE))
    except Exception: pass
    pairs=read_docs(folder)
    payloads,texts=[],[]
    for path,full in pairs:
        for part in chunk(full):
            payloads.append({"source":path,"text":part})
            texts.append(part)
    if not texts: print("No texts found"); return
    embs=embed(texts)
    cli.upsert(COLLECTION, points=qm.Batch(ids=list(range(len(embs))), vectors=embs, payloads=payloads))
    print(f"Indexed {len(embs)} chunks into {COLLECTION}")
if __name__=="__main__":
    import sys; main(sys.argv[1] if len(sys.argv)>1 else "./data")
