import pandas as pd


class DetectionStore:

    def __init__(self):
        self.records = []

    @staticmethod
    def _centers(boxes):
        centers = (boxes[:, :2] + boxes[:, 2:]) / 2
        return centers

    def add(self, detections, frame_id=None, timestamp=None):
        """
        Guarda detections de un frame.
        """

        if detections is None or len(detections) == 0:
            return

        boxes = detections.xyxy
        centers = self._centers(boxes)

        conf = getattr(detections, "confidence", None)
        cls = getattr(detections, "class_id", None)
        tid = getattr(detections, "tracker_id", None)

        for i in range(len(boxes)):
            record = {
                "frame": frame_id,
                "timestamp": timestamp,

                # "x1": boxes[i, 0],
                # "y1": boxes[i, 1],
                # "x2": boxes[i, 2],
                # "y2": boxes[i, 3],

                "cx": centers[i, 0],
                "cy": centers[i, 1],
            }

            if conf is not None:
                record["confidence"] = conf[i]

            if cls is not None:
                record["class_id"] = cls[i]

            if tid is not None:
                record["tracker_id"] = tid[i]

            self.records.append(record)

    def to_dataframe(self):
        return pd.DataFrame(self.records)

    def clear(self):
        self.records = []
