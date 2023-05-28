import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout


class HelloWorldApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Create a button
        self.button = QPushButton('Click me!', self)
        self.button.clicked.connect(self.buttonClicked)

        # Create a label
        self.label = QLabel(self)

        # Create a vertical layout and add the button and label
        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.label)

        # Set the layout for the main window
        self.setLayout(layout)

        self.setWindowTitle('Hello, World!')
        self.show()

    def buttonClicked(self):
        self.label.setText('Button clicked!')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    hello_world = HelloWorldApp()
    sys.exit(app.exec_())
