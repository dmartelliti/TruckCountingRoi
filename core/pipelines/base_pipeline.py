from abc import ABC, abstractmethod


class BasePipeline(ABC):

    name: str = "base_pipeline"

    @abstractmethod
    def process(self, *args, **kwargs):
        raise NotImplementedError