import numpy as np


def embedding_from_bytes(
    byt: bytes, counts: list[int], embedding_length: int, dtype: np.dtype = np.float32
) -> np.ndarray:
    start = 0
    embedding = []
    el = embedding_length // np.dtype(dtype).itemsize
    for count in counts:
        embs: list[np.ndarray] = []
        for _ in range(count):
            end = start + embedding_length
            emb = np.frombuffer(byt[start:end], dtype=dtype)
            if emb.shape[0] != el:
                raise ValueError(
                    f"Invalid embedding length, expected {el}, got {emb.shape[0]}"
                )
            embs.append(emb)
            start = end

        # TODO 결과 잘 안나오면 평균으로 수정
        ary = np.array([e for e in embs if e.shape[0] > 0])
        ary_sum = np.sum(ary, axis=0)
        embedding.append(ary_sum)
    return np.array(embedding)


__all__ = [
    "embedding_from_bytes",
]
