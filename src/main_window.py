from pathlib import Path
import json

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor, QKeyEvent, QCloseEvent, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QGroupBox,
    QCheckBox,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
)

from .graphics_view import GraphicsView


class MainWindow(QMainWindow):
    brush_feedback = pyqtSignal(int)  # allows QSlider react on mouse wheel
    autoseg_signal = pyqtSignal(bool)  # used to propagate autosegmentation mode to all widgets

    def __init__(self, workdir: str):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Annotator")
        self.resize(1000, 1000)

        self._workdir = Path(workdir)
        self._class_dir = self._workdir / "classes.json"
        self._image_dir = self._workdir / "images"
        self._label_dir = self._workdir / "labels"
        self._autoseg_dir = self._workdir / "autoseg"
        self._label_dir.mkdir(exist_ok=True)
        self._autoseg_dir.mkdir(exist_ok=True)
        self._image_stems = [path.stem for path in sorted(self._image_dir.iterdir())]
        with open(self._class_dir, "r") as f:
            self._classes = json.loads("".join(f.readlines()))["classes"]
        ids = [c["id"] for c in self._classes]
        colors = [c["color"] for c in self._classes]
        self._id2color = {k: v for k, v in zip(ids, colors)}

        self.brush_feedback.connect(self.on_brush_size_change)
        self._graphics_view = GraphicsView(self.brush_feedback)
        self.autoseg_signal.connect(self._graphics_view.handle_autoseg_signal)

        # Dataset group
        ds_group = QGroupBox(self.tr("Dataset"))

        self.ds_label = QLabel()
        self.ds_label.setText("Sample: 000000.png")

        ds_vlay = QVBoxLayout(ds_group)
        ds_vlay.addWidget(self.ds_label)

        # Layers group
        ls_group = QGroupBox(self.tr("Layers"))

        self.ls_label_value = QLabel()
        self.ls_label_value.setText("Label opacity: 50%")

        self.ls_label_slider = QSlider()
        self.ls_label_slider.setOrientation(Qt.Orientation.Horizontal)
        self.ls_label_slider.setMinimum(0)
        self.ls_label_slider.setMaximum(100)
        self.ls_label_slider.setSliderPosition(50)
        self.ls_label_slider.valueChanged.connect(self.on_ls_label_slider_change)

        self.ls_autoseg_value = QLabel()
        self.ls_autoseg_value.setText("autoseg opacity: 20%")

        self.ls_autoseg_slider = QSlider()
        self.ls_autoseg_slider.setOrientation(Qt.Orientation.Horizontal)
        self.ls_autoseg_slider.setMinimum(0)
        self.ls_autoseg_slider.setMaximum(100)
        self.ls_autoseg_slider.setSliderPosition(0)
        self.ls_autoseg_slider.valueChanged.connect(self.on_ls_autoseg_slider_change)

        ls_vlay = QVBoxLayout(ls_group)
        ls_vlay.addWidget(self.ls_label_value)
        ls_vlay.addWidget(self.ls_label_slider)
        ls_vlay.addWidget(self.ls_autoseg_value)
        ls_vlay.addWidget(self.ls_autoseg_slider)

        # AUTOSEG group
        autoseg_group = QGroupBox(self.tr("AUTOSEG"))

        self.autoseg_checkbox = QCheckBox("AUTOSEG assistance")
        self.autoseg_checkbox.stateChanged.connect(self.on_autoseg_change)

        autoseg_vlay = QVBoxLayout(autoseg_group)
        autoseg_vlay.addWidget(self.autoseg_checkbox)

        # Brush size group
        bs_group = QGroupBox(self.tr("Brush"))

        self.bs_value = QLabel()
        self.bs_value.setText("Size: 50 px")

        self.bs_slider = QSlider()
        self.bs_slider.setOrientation(Qt.Orientation.Horizontal)
        self.bs_slider.setMinimum(1)
        self.bs_slider.setMaximum(150)
        self.bs_slider.setSliderPosition(50)
        self.bs_slider.valueChanged.connect(self.on_bs_slider_change)

        bs_vlay = QVBoxLayout(bs_group)
        bs_vlay.addWidget(self.bs_value)
        bs_vlay.addWidget(self.bs_slider)

        # Classs selection group
        cs_group = QGroupBox(self.tr("Classes"))

        self.cs_list = QListWidget()
        for i, c in enumerate(self._classes):
            color = QColor(c["color"])
            pixmap = QPixmap(20, 20)
            pixmap.fill(color)
            text = f"[{i+1}] {c['name']}"
            item = QListWidgetItem(QIcon(pixmap), text)
            self.cs_list.addItem(item)
        self.cs_list.itemClicked.connect(self.on_item_clicked)

        cs_vlay = QVBoxLayout(cs_group)
        cs_vlay.addWidget(self.cs_list)

        vlay = QVBoxLayout()
        vlay.addWidget(ds_group)
        vlay.addWidget(autoseg_group)
        vlay.addWidget(ls_group)
        vlay.addWidget(bs_group)
        vlay.addWidget(cs_group)
        vlay.addStretch()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        lay = QHBoxLayout(central_widget)
        lay.addWidget(self._graphics_view, stretch=1)
        lay.addLayout(vlay, stretch=0)

        self._curr_id = 0
        self._graphics_view.set_brush_color(QColor(colors[0]))
        self.cs_list.setCurrentRow(0)

    @pyqtSlot(int)
    def on_autoseg_change(self, state: int):
        if state == Qt.CheckState.Checked:
            self.autoseg_signal.emit(True)
        elif state == Qt.CheckState.Unchecked:
            self.autoseg_signal.emit(False)
        else:
            print("unsupported check state")

    @pyqtSlot(int)
    def on_ls_label_slider_change(self, value: int):
        self.ls_label_value.setText(f"Label opacity: {value}%")
        self._graphics_view.set_label_opacity(value)

    @pyqtSlot(int)
    def on_ls_autoseg_slider_change(self, value: int):
        self.ls_autoseg_value.setText(f"AUTOSEG opacity: {value}%")
        self._graphics_view.set_autoseg_opacity(value)

    @pyqtSlot(int)
    def on_bs_slider_change(self, value: int):
        self.bs_value.setText(f"Size: {value} px")
        self._graphics_view.set_brush_size(value)

    @pyqtSlot(int)
    def on_brush_size_change(self, value: int):
        # updates slider and value label on brush size change via mouse wheel
        self.bs_value.setText(f"Size: {value} px")
        self.bs_slider.setSliderPosition(value)

    def on_item_clicked(self, item: QListWidgetItem):
        idx = self.sender().currentRow()
        color = self._id2color[idx + 1]
        self._graphics_view.set_brush_color(QColor(color))

    def save_current_label(self):
        curr_label_path = self._label_dir / f"{self._image_stems[self._curr_id]}.png"
        self._graphics_view.save_label_to(curr_label_path)

    def _load_sample_by_id(self, id: int):
        self._curr_id = id
        name = f"{self._image_stems[self._curr_id]}.png"
        image_path = self._image_dir / name
        label_path = self._label_dir / name
        autoseg_path = self._autoseg_dir / name
        self._graphics_view.load_sample(image_path, label_path, autoseg_path)
        self.ds_label.setText(f"Sample: {name}")

    def load_latest_sample(self):
        labels = list(self._label_dir.iterdir())
        images = list(self._image_dir.iterdir())
        if len(labels) < len(images):
            self._load_sample_by_id(len(labels))
        else:
            self._load_sample_by_id(0)

    def _switch_sample_by(self, step: int):
        if step == 0:
            return
        self.save_current_label()
        max_id = len(self._image_stems) - 1
        corner_case_id = 0 if step < 0 else max_id
        new_id = self._curr_id + step
        new_id = new_id if new_id in range(max_id + 1) else corner_case_id
        self._load_sample_by_id(new_id)

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        if a0.key() == Qt.Key.Key_Space:
            self._graphics_view.reset_zoom()
        elif a0.key() == Qt.Key.Key_A:
            self.autoseg_checkbox.toggle()
        elif a0.key() == Qt.Key.Key_C:
            self._graphics_view.clear_label()
        elif a0.key() == Qt.Key.Key_E:
            self.cs_list.clearSelection()
            self._graphics_view.set_eraser(True)
        elif a0.key() in range(49, 58):
            num_key = int(a0.key()) - 48
            color = self._id2color.get(num_key)
            if color:
                self._graphics_view.set_brush_color(QColor(color))
                self.cs_list.setCurrentRow(num_key - 1)
        elif a0.key() == Qt.Key.Key_Comma:
            self._switch_sample_by(-1)
        elif a0.key() == Qt.Key.Key_Period:
            self._switch_sample_by(1)

        return super().keyPressEvent(a0)

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.save_current_label()
        return super().closeEvent(a0)
