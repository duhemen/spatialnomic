"""
SpatiaNomics - PyQt6 Desktop Client Entry Point
"""
import sys
from loguru import logger
from PyQt6.QtWidgets import QApplication
from client.gui.main_window import MainWindow


def main():
    logger.add("logs/client.log", rotation="5 MB")
    logger.info("🚀 SpatiaNomics Client starting...")

    app = QApplication(sys.argv)
    app.setApplicationName("SpatiaNomics")

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()