from abc import ABC, abstractmethod
from ....utils import current_seconds


class ResourceHandler(ABC):

    def __init__(self) -> None:
        self.access_time = current_seconds()
        self.max_timeout: float = 120.0 # 2 mins

    @abstractmethod
    async def initial(self):
        pass


    # for calling outside
    async def access(self, **kwargs):
        # DO pre process
        self._update_access_time()
        result = await self.accessing(**kwargs)
        # DO post process...
        return result

    # # child class implements this function
    @abstractmethod
    async def accessing(self, **kwargs):
        pass

    # 定期激活，維持連線和連線池
    # Regular activation to maintain connections and connection pools
    @abstractmethod
    async def probe(self):
        pass

    @abstractmethod
    async def close(self):
        pass

    def _update_access_time(self):
        self.access_time = current_seconds()

    def timeout(self) -> bool:
        connect_time = current_seconds() - self.access_time
        return self.max_timeout < connect_time
