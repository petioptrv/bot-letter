from abc import ABC, abstractmethod

from app.base_types import CacheItem


class CacheBase(ABC):
    @abstractmethod
    def store_item(self, cache_item: CacheItem):
        ...
