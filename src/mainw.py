import concurrent.futures
import json
import os.path
import shutil
import sys
import time
from pathlib import Path
from PyQt5.QtCore import Qt, QRunnable, pyqtSlot, QThreadPool, QUrl
from PyQt5.QtGui import QFont, QIcon, QPixmap, QDesktopServices
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QPushButton, QCheckBox, QColorDialog, \
    QDoubleSpinBox, QSpinBox, QGridLayout, QScrollArea, QFileDialog, QTableWidgetItem, QHeaderView
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


def process_image(data):
    stats_config: OcrStatsConfig
    image_path, config, stats_config, save_stats, target_folder = data
    target_folder = Path(target_folder) / os.path.basename(image_path)

    if save_stats:
        stats_config.set_enabled_true(target_folder)

    start_time = time.perf_counter()
    ocr = Ocr(config, stats_config)
    try:
        ocr.image_ocr(image_path)
    except (Exception, ):
        return False, image_path, time.time() - start_time

    if not stats_config.is_enabled:
        if not target_folder.exists():
            target_folder.mkdir(parents=True)
        result = ocr.get_data_as_text()
        with open(target_folder / "output.txt", "w") as f:
            f.write(result)
    res_time = round(time.perf_counter() - start_time, 2)
    return True, image_path, res_time


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("gui.ui", self)
        self.threadpool = QThreadPool()

        self.files = []
        self.prev_files = []
        self.config = OcrConfig()
        self.stats_config = OcrStatsConfig()
        self.init()

        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnWidth(0, 10)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tableWidget.setColumnWidth(3, 10)
        self.tableWidget.setColumnWidth(4, 10)
        self.tableWidget.itemClicked.connect(self.table_item_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.json_to_widget(self.config.to_json()))
        self.configTab.setLayout(layout)

        layout = QVBoxLayout()
        layout.addWidget(self.json_to_widget(self.stats_config.to_json()))
        self.statsConfigTab.setLayout(layout)

        self.update_labels()
        self.tabsWidget.setCurrentIndex(0)

        self.pathButton.clicked.connect(self.select_path_dialog)
        self.runButton.clicked.connect(self.run_clicked)
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
            self.update_files_line()

    def update_files_line(self):
        files = [os.path.basename(path) for path in self.files]
        self.pathLine.setText(", ".join(files))
        if len(self.files) == 0:
            self.runButton.setEnabled(False)
        else:
            self.runButton.setEnabled(True)

    def table_item_clicked(self, item):
        row = item.row()
        if row > len(self.prev_files) - 1:
            return
        if item.column() == 3:
            path = os.path.join("out", os.path.basename(self.prev_files[row]))
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        if item.column() == 4:
            path = os.path.join("out", os.path.basename(self.prev_files[row]), "output.txt")
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def run_clicked(self):
        self.prev_files = self.files
        worker = Worker(self)
        self.threadpool.start(worker)

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

    def handle_table_row(self, row, flag, image_name, time_v):
        self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)
        self.tableWidget.setItem(row, 1, QTableWidgetItem(image_name))
        if not flag:
            icon = QIcon(QPixmap(str(Path("resources/failure.png"))))
            item = QTableWidgetItem()
            item.setIcon(icon)
            self.tableWidget.setItem(row, 0, item)
        else:
            icon = QIcon(QPixmap(str(Path("resources/success.png"))))
            item = QTableWidgetItem()
            item.setIcon(icon)
            self.tableWidget.setItem(row, 0, item)

            item = QTableWidgetItem(str(time_v) + " sec")
            item.setTextAlignment(Qt.AlignRight)
            self.tableWidget.setItem(row, 2, item)

            icon = QIcon(QPixmap(str(Path("resources/folder_2.png"))))
            item = QTableWidgetItem()
            item.setIcon(icon)
            self.tableWidget.setItem(row, 3, item)

            icon = QIcon(QPixmap(str(Path("resources/txt.png"))))
            item = QTableWidgetItem()
            item.setIcon(icon)
            self.tableWidget.setItem(row, 4, item)
        self.tableWidget.viewport().update()


class Worker(QRunnable):
    def __init__(self, window: MainWidget):
        super().__init__()
        self.w = window

    @pyqtSlot()
    def run(self):
        self.w.tabsContainerWidget.setEnabled(False)
        self.w.panelContainerWidget.setEnabled(False)

        self.w.tableWidget.clearContents()
        self.w.tableWidget.setRowCount(0)
        self.w.tableWidget.setColumnCount(5)

        self.w.stats_config.set_enabled_false()
        if os.path.exists("out"):
            shutil.rmtree("out")

        data = []
        for i in range(len(self.w.files)):
            data.append((self.w.files[i], self.w.config, self.w.stats_config, self.w.statsCheckBox.isChecked(), "out"))

        start_time = time.perf_counter()
        if self.w.multiprocessingCheckBox.isChecked():
            with concurrent.futures.ProcessPoolExecutor() as exe:
                results = exe.map(process_image, data)
                for i, (flag, image_path, time_v) in enumerate(results):
                    self.w.handle_table_row(i, flag, os.path.basename(image_path), time_v)
        else:
            for i, v in enumerate(data):
                flag, image_path, time_v = process_image(v)
                self.w.handle_table_row(i, flag, os.path.basename(image_path), time_v)
        res_time = round(time.perf_counter() - start_time, 2)

        self.w.tableWidget.setRowCount(self.w.tableWidget.rowCount() + 1)
        item = QTableWidgetItem(str(res_time) + " sec")
        item.setTextAlignment(Qt.AlignRight)
        self.w.tableWidget.setItem(len(self.w.files), 2, item)

        self.w.tabsContainerWidget.setEnabled(True)
        self.w.panelContainerWidget.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWidget()
    ex.show()
    sys.exit(app.exec_())
