from typing import List

import numpy as np

from app.base_types import CacheItem
from app.core.selection_algos.duplicates_remover import DuplicatesRemover


class RepresentativeItemsAlgo:
    # todo: make it exclude duplicated articles
    # todo: make it exclude outliers
    def __init__(self, duplicates_remover: DuplicatesRemover):
        self._duplicates_remover = duplicates_remover

    async def get_k_most_representative_items(
        self, new_items: List[CacheItem], cache_items: List[CacheItem], k: int
    ) -> List[CacheItem]:
        new_items_matrix = np.array([item.embedding.vector for item in new_items])
        cache_items_matrix = np.array([item.embedding.vector for item in cache_items])
        average_vector = np.average(cache_items_matrix, axis=0)
        distances_from_average = np.linalg.norm(new_items_matrix - average_vector, axis=1)
        sorted_indices = np.argsort(distances_from_average)
        sorted_items = [new_items[i] for i in sorted_indices[:k]]
        # processed_items_count = k
        # done = False
        # while not done:
        #     sorted_items = await self._remove_duplicated_articles(items=sorted_items)
        #     if len(sorted_items) == k:
        #         done = True
        #     else:
        #         sorted_items = (
        #             sorted_items + [
        #                 items[i] for i in sorted_indices[processed_items_count:processed_items_count + k - len(sorted_items)]
        #             ]
        #         )
        #         processed_items_count += k - len(sorted_items)

        return sorted_items

    async def _remove_duplicated_articles(self, items: [CacheItem]) -> [CacheItem]:
        return await self._duplicates_remover.remove_duplicated_articles(items=items)

    @staticmethod
    def _reject_outliers(data: np.ndarray, m: int = 2):
        distances_from_median = np.abs(data - np.median(data))
        median_deviation = np.median(distances_from_median)
        s = distances_from_median / median_deviation if median_deviation else np.zeros(len(distances_from_median))
        return data[s < m]
