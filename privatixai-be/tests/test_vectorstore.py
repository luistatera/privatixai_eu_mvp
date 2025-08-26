import os
from pathlib import Path
from vectorstore.chroma_store import add_documents, get_stats


def test_chroma_upsert_and_stats(tmp_path: Path, monkeypatch):
    # Isolate storage dirs
    vs_dir = tmp_path / "vectorstore"
    chunks_dir = tmp_path / "chunks"
    vs_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("PRIVATIXAI_VECTORSTORE_PATH", str(vs_dir))
    monkeypatch.setenv("PRIVATIXAI_CHUNKS_PATH", str(chunks_dir))

    documents = [
        "first chunk text",
        "second chunk text",
    ]
    metadatas = [
        {"file_id": "f1", "chunk_id": "c1", "start": 0, "end": 10},
        {"file_id": "f1", "chunk_id": "c2", "start": 10, "end": 20},
    ]
    ids = ["c1", "c2"]

    add_documents(documents=documents, metadatas=metadatas, ids=ids)

    stats = get_stats()
    assert stats["chunks"] >= 2
    # files may be 1 based on metadata
    assert stats["files"] in (None, 1, 2)


