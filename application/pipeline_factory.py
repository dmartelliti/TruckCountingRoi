from core.pipelines.truck_counter_pipeline import TruckCounterPipeline


class PipelineFactory:

    @staticmethod
    def create(name):

        if name == "truck_counter":
            return TruckCounterPipeline()

        raise ValueError(f"Unknown pipeline: {name}")