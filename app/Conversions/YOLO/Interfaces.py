from odmetrics.bounding_box import ValBoundingBox


class IYOLODetection:
    def __init__(
            self,
            class_id: int,
            x_center: float,
            y_center: float,
            width: float,
            height: float,
            confidence: float = 1.0,
    ):
        self.x_center = x_center
        self.y_center = y_center
        self.width = width
        self.height = height
        self.class_id = class_id
        self.confidence = confidence

    def to_val_box(self, image_id: int | str, image_size: tuple[int, int],
                   ground_truth: bool = False) -> ValBoundingBox:
        raise NotImplementedError()

    def __str__(self):
        return f"{self.class_id} {self.x_center:.6f} {self.y_center:.6f} {self.width:.6f} {self.height:.6f}"


class IYOLOFullPageDetection:
    def __init__(
            self,
            image_size: tuple[int, int],
            annotations: list[IYOLODetection],
    ):
        self.image_size = image_size
        self.annotations = annotations


class IYOLOSegmentation:
    def __init__(
            self,
            class_id: int,
            coordinates: list[tuple[float, float]],
            confidence: float = 1.0,
    ):
        self.coordinates = coordinates
        self.class_id = class_id
        self.confidence = confidence

    def __str__(self):
        coords = " ".join([f"{point[0]:.6f} {point[1]:.6f}" for point in self.coordinates])
        return f"{self.class_id} {coords}"


class IYOLOFullPageSegmentation:
    def __init__(
            self,
            image_size: tuple[int, int],
            annotations: list[IYOLOSegmentation],
    ):
        self.image_size = image_size
        self.annotations = annotations
