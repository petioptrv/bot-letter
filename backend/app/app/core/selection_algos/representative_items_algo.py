from typing import List, Generator

import numpy as np

from app.base_types import CacheItem


async def generate_most_representative_items(
    target_vector: np.ndarray, cache_items: List[CacheItem]
) -> Generator[CacheItem, None, None]:
    cache_items_matrix = np.array([item.embedding.vector for item in cache_items])
    similarities = _cosine_similarity_matrix(matrix=cache_items_matrix, vector=target_vector)
    sorted_indices = np.argsort(similarities)
    for index in sorted_indices[::-1]:
        yield cache_items[index]


def _cosine_similarity_matrix(matrix: np.ndarray, vector: np.ndarray) -> np.ndarray:
    norm_matrix = np.linalg.norm(matrix, axis=1)
    norm_vector = np.linalg.norm(vector)
    similarities = np.dot(matrix, vector) / (norm_matrix * norm_vector)
    return similarities
