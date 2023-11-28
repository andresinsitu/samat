from pathlib import Path

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsSceneMouseEvent,
)
from PyQt5.QtCore import pyqtSignal, QPointF

from .brush_cursor import BrushCursor
from .label_layer import LabelLayer
from .autoseg_layer import AutosegLayer

import numpy as np


class GraphicsScene(QGraphicsScene):
    #TODO: cambiar label2autoseg_signal a np.ndarray
    label2autoseg_signal = pyqtSignal(QPointF,int)
    autoseg2label_signal = pyqtSignal(list)

    def __init__(self, parent):
        super().__init__(parent)
        self._brush_size = 50
        self._brush_step = 1
        self._brush_limits = (1, 150)

        self.image_item = QGraphicsPixmapItem()
        self.autoseg_item = AutosegLayer(self.image_item, self.autoseg2label_signal)
        self.label_item = LabelLayer(self.image_item, self.label2autoseg_signal)
        self.cursor_item = BrushCursor(self.image_item)

        self.label2autoseg_signal.connect(self.autoseg_item.handle_click)
        self.autoseg2label_signal.connect(self.label_item.handle_bundle)

        self.addItem(self.image_item)

    def handle_autoseg_mode(self, is_autoseg: bool):
        self.autoseg_item.handle_autoseg_mode(is_autoseg)
        self.label_item.handle_autoseg_mode(is_autoseg)
        self._autoseg_mode = is_autoseg

    def set_eraser(self, value):
        self.label_item.set_eraser(value)
        if value:
            self.cursor_item.set_border_color(QColor(255, 255, 255))

    def set_brush_color(self, color: QColor):
        self.cursor_item.set_border_color(color)
        self.label_item.set_brush_color(color)

    def set_brush_size(self, value: int):
        assert self._brush_limits[0] <= value <= self._brush_limits[1]
        self._brush_size = value
        self.cursor_item.set_size(self._brush_size)
        self.label_item.set_size(self._brush_size)

    def change_brush_size(self, sign: int, bf: pyqtSignal):
        # fmt: off
        assert sign in (-1, 1), f"Sign value must be either 1 or -1, but {sign} was given"  # noqa: E501
        # fmt: on
        new_size = self._brush_size + (self._brush_step * sign)
        new_size = max(new_size, self._brush_limits[0])
        new_size = min(new_size, self._brush_limits[1])
        self.cursor_item.set_size(new_size)
        self.label_item.set_size(new_size)
        self._brush_size = new_size
        bf.emit(new_size)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.cursor_item.setPos(event.scenePos())
        super().mouseMoveEvent(event)

    def save_label(self, label_path: Path):
        self.label_item.export_pixmap(label_path)
