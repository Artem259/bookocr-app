import json
import math
import os.path
import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QSlider, QTabWidget, QPushButton, QCheckBox, \
    QColorDialog, QDoubleSpinBox, QSpinBox, QHBoxLayout, QGridLayout, QScrollArea, QSizePolicy, QFileDialog
from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from bookocr.ocr import Ocr
from bookocr.config import OcrConfig
from bookocr.stats_config import OcrStatsConfig


def create_lambda(function, *args, **kwargs):
    return lambda: function(*args, **kwargs)


def write_json_file(file_path, dictionary, *args, **kwargs):
    try:
        with open(file_path, "w") as file:
            json.dump(dictionary, file, *args, **kwargs)
        return True
    except IOError:
        return False


def read_json_file(file_path):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return None


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("gui.ui", self)

        self.files = []
        self.config = OcrConfig()
        self.stats_config = OcrStatsConfig()
        self.init()

        layout = QVBoxLayout()
        layout.addWidget(self.json_to_widget(self.config.to_json()))
        self.configTab.setLayout(layout)

        layout = QVBoxLayout()
        layout.addWidget(self.json_to_widget(self.stats_config.to_json()))
        self.statsConfigTab.setLayout(layout)

        self.update_labels()
        self.tabsWidget.setCurrentIndex(0)

        self.pathButton.clicked.connect(self.select_path_dialog)
        self.restoreButton.clicked.connect(self.restore_clicked)
        self.applyButton.clicked.connect(self.apply_clicked)
        self.restoreDefaultsButton.clicked.connect(self.restore_defaults_clicked)

    def init(self):
        data = read_json_file(Path("data/data.json"))
        if data is not None:
            self.setGeometry(*data["geometry"])
            self.files = data["files"]
            self.statsCheckBox.setChecked(data["save_stats"])
            self.multiprocessingCheckBox.setChecked(data["use_multiprocessing"])
        self.update_files_line()

        try:
            self.config = OcrConfig.from_json_file(Path("data/config.json"))
        except (Exception, ):
            self.config = OcrConfig()

        try:
            self.stats_config = OcrStatsConfig.from_json_file(Path("data/stats_config.json"))
        except (Exception,):
            self.stats_config = OcrStatsConfig()

    def closeEvent(self, event):
        if not os.path.exists("data"):
            os.makedirs("data")

        data = {"geometry": self.geometry().getRect(),
                "files": self.files,
                "save_stats": self.statsCheckBox.isChecked(),
                "use_multiprocessing": self.multiprocessingCheckBox.isChecked()}
        write_json_file(Path("data/data.json"), data, indent=4)

        try:
            self.config.to_json_file(Path("data/config.json"), indent=4)
            self.stats_config.to_json_file(Path("data/stats_config.json"), indent=4)
        except (Exception, ):
            return

    def config_value_changed(self, label: QLabel):
        font = QFont(label.font().family(), label.font().pointSize(), QFont.DemiBold)
        label.setFont(font)
        if label.text()[-1] != "*":
            label.setText(label.text() + "*")
        self.applyButton.setEnabled(True)
        self.restoreButton.setEnabled(True)

    def select_color_dialog(self, button, label):
        color = QColorDialog.getColor()
        if color.isValid():
            r, g, b, _ = color.getRgb()
            button.setStyleSheet(f"background-color: rgb({r}, {g}, {b})")
            button.setText(button.palette().color(button.backgroundRole()).name())
            self.config_value_changed(label)

    def select_path_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")
        if files:
            self.files = files
            self.runButton.setEnabled(True)
            self.update_files_line()

    def update_files_line(self):
        self.pathLine.setText(", ".join(self.files))

    def restore_clicked(self):
        self.update_widget_from_object(self.configTab, self.config)
        self.update_widget_from_object(self.statsConfigTab, self.stats_config)
        self.update_labels()
        self.applyButton.setEnabled(False)
        self.restoreButton.setEnabled(False)

    def apply_clicked(self):
        self.config = OcrConfig.from_json(self.json_from_widget(self.configTab))
        self.stats_config = OcrStatsConfig.from_json(self.json_from_widget(self.statsConfigTab))
        self.update_labels()
        self.applyButton.setEnabled(False)
        self.restoreButton.setEnabled(False)

    def restore_defaults_clicked(self):
        self.config = OcrConfig()
        self.stats_config = OcrStatsConfig()
        self.restore_clicked()

    def update_labels(self):
        self.update_widget_labels(self.configTab, self.config, OcrConfig())
        self.update_widget_labels(self.statsConfigTab, self.stats_config, OcrStatsConfig())

    def json_to_widget(self, json_string):
        data = json.loads(json_string)

        layout = QGridLayout()
        layout.setColumnStretch(1, 1)
        layout.setAlignment(Qt.AlignTop)

        widget = QWidget()
        widget.setLayout(layout)

        row = 0
        for key, value in data.items():
            label = QLabel(key)
            layout.addWidget(label, row, 0)

            if isinstance(value, bool):
                check_box = QCheckBox()
                check_box.setChecked(value)
                layout.addWidget(check_box, row, 1)

                check_box.stateChanged.connect(create_lambda(self.config_value_changed, label))

            elif isinstance(value, float):
                spin_box = QDoubleSpinBox()
                spin_box.setMinimum(0)
                spin_box.setMaximum(1000000)
                spin_box.setValue(value)
                layout.addWidget(spin_box, row, 1)

                spin_box.valueChanged.connect(create_lambda(self.config_value_changed, label))

            elif isinstance(value, int):
                spin_box = QSpinBox()
                spin_box.setMinimum(0)
                spin_box.setMaximum(1000000)
                spin_box.setValue(value)
                layout.addWidget(spin_box, row, 1)

                spin_box.valueChanged.connect(create_lambda(self.config_value_changed, label))

            elif isinstance(value, list) and len(value) == 3:
                color_button = QPushButton()

                b, g, r = value
                color_button.setStyleSheet(f"background-color: rgb({r}, {g}, {b})")
                layout.addWidget(color_button, row, 1)
                color_button.setText(color_button.palette().color(color_button.backgroundRole()).name())

                color_button.clicked.connect(create_lambda(self.select_color_dialog, color_button, label))
            else:
                raise RuntimeError("Unknown type.")
            row += 1

        layout.setHorizontalSpacing(30)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(widget)

        return scroll_area

    def json_from_widget(self, widget):
        data = {}
        layout = widget.findChild(QGridLayout)
        for row in range(layout.rowCount()):
            label_item = layout.itemAtPosition(row, 0)
            widget_item = layout.itemAtPosition(row, 1)

            label = label_item.widget().text()
            widget = widget_item.widget()

            if label[-1] == "*":
                label = label[:-1]

            if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                data[label] = widget.value()
            elif isinstance(widget, QCheckBox):
                data[label] = widget.isChecked()
            elif isinstance(widget, QPushButton):
                r, g, b, _ = widget.palette().color(widget.backgroundRole()).getRgb()
                data[label] = (b, g, r)
            else:
                raise RuntimeError("Unknown widget.")

        return json.dumps(data, indent=4)

    def update_widget_from_object(self, widget, obj):
        layout = widget.findChild(QGridLayout)
        for row in range(layout.rowCount()):
            label_item = layout.itemAtPosition(row, 0)
            widget_item = layout.itemAtPosition(row, 1)

            label = label_item.widget().text()
            widget = widget_item.widget()

            if label[-1] == "*":
                label = label[:-1]
            value = getattr(obj, label)

            if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                widget.setValue(value)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(value)
            elif isinstance(widget, QPushButton):
                b, g, r = value
                widget.setStyleSheet(f"background-color: rgb({r}, {g}, {b})")
                widget.setText(widget.palette().color(widget.backgroundRole()).name())
            else:
                raise RuntimeError("Unknown widget.")

    def update_widget_labels(self, widget, saved_obj, default_obj):
        layout = widget.findChild(QGridLayout)
        for row in range(layout.rowCount()):
            label_item = layout.itemAtPosition(row, 0)
            widget_item = layout.itemAtPosition(row, 1)

            label_widget = label_item.widget()
            label = label_widget.text()
            widget = widget_item.widget()

            if label[-1] == "*":
                label = label[:-1]
            saved_value = getattr(saved_obj, label)
            default_value = getattr(default_obj, label)

            if isinstance(saved_value, list):
                saved_value = tuple(saved_value)
            if isinstance(default_value, list):
                default_value = tuple(default_value)

            if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                value = widget.value()
            elif isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, QPushButton):
                r, g, b, _ = widget.palette().color(widget.backgroundRole()).getRgb()
                value = (b, g, r)
            else:
                raise RuntimeError("Unknown widget.")

            label_widget.setText(label)
            font = QFont(label_widget.font().family(), label_widget.font().pointSize())
            label_widget.setFont(font)
            if value != saved_value:
                label_widget.setText(label + "*")
            if saved_value != default_value:
                font = QFont(label_widget.font().family(), label_widget.font().pointSize(), QFont.DemiBold)
                label_widget.setFont(font)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWidget()
    ex.show()
    sys.exit(app.exec_())
