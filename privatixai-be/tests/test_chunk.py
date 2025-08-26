from ingestion.chunk import fixed_size_chunk


def test_fixed_size_chunk_counts_and_boundaries():
    text = "a" * 2500
    size = 1000
    overlap = 200

    chunks = fixed_size_chunk(text, size, overlap)

    # Expect 3 chunks with specific boundaries
    assert len(chunks) == 3
    assert chunks[0][0] == 0 and chunks[0][1] == 1000
    assert chunks[1][0] == 800 and chunks[1][1] == 1800
    assert chunks[2][0] == 1600 and chunks[2][1] == 2500


