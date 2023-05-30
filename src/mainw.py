import json
import math
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QSlider, QTabWidget, QPushButton, QCheckBox, \
    QColorDialog, QDoubleSpinBox, QSpinBox, QHBoxLayout, QGridLayout, QScrollArea, QSizePolicy
from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from bookocr.ocr import Ocr
from bookocr.config import OcrConfig
from bookocr.stats_config import OcrStatsConfig


def create_lambda(self, function, *args, **kwargs):
    return lambda: function(*args, **kwargs)


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("gui.ui", self)

        cg = OcrConfig()
        layout = QGridLayout()
        layout.addWidget(self.generate_widget_from_json(cg.to_json()))
        self.configTab.setLayout(layout)

        scg = OcrStatsConfig()
        layout = QGridLayout()
        layout.addWidget(self.generate_widget_from_json(scg.to_json()))
        self.statsConfigTab.setLayout(layout)

        self.tabsWidget.setCurrentIndex(0)

    def config_value_changed(self, label: QLabel):
        font = QFont(label.font().family(), label.font().pointSize(), QFont.DemiBold)
        label.setFont(font)
        self.applyButton.setEnabled(True)

    def select_color_dialog(self, button, _label):
        color = QColorDialog.getColor()
        if color.isValid():
            color_v = color.getRgb()
            button.setStyleSheet(f"background-color: rgb({color_v[0]}, {color_v[1]}, {color_v[2]})")
            self.config_value_changed(_label)

    def generate_widget_from_json(self, json_string):
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

                check_box.stateChanged.connect(self.create_lambda(self.config_value_changed, label))

            elif isinstance(value, float):
                spin_box = QDoubleSpinBox()
                spin_box.setValue(value)
                spin_box.setMinimum(0)
                spin_box.setMaximum(1000000)
                layout.addWidget(spin_box, row, 1)

                spin_box.valueChanged.connect(self.create_lambda(self.config_value_changed, label))

            elif isinstance(value, int):
                spin_box = QSpinBox()
                spin_box.setValue(value)
                spin_box.setMinimum(0)
                spin_box.setMaximum(1000000)
                layout.addWidget(spin_box, row, 1)

                spin_box.valueChanged.connect(self.create_lambda(self.config_value_changed, label))

            elif isinstance(value, list) and len(value) == 3:
                color_button = QPushButton()

                color_button.setStyleSheet(f"background-color: rgb({value[2]}, {value[1]}, {value[0]})")
                color_button.clicked.connect(self.create_lambda(self.select_color_dialog, color_button, label))
                layout.addWidget(color_button, row, 1)
            else:
                value_label = QLabel(str(value))
                layout.addWidget(value_label, row, 1, 1, 2)
            row += 1

        layout.setHorizontalSpacing(20)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(widget)

        return scroll_area


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWidget()
    ex.show()
    sys.exit(app.exec_())
