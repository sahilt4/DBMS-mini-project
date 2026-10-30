"""
Smart Bus Reservation System - Main Application Entry Point
College DBMS Mini Project | Native Python Desktop Application
Built with PySide6 & SQLite.
"""
import sys
import logging
from pathlib import Path

# Add project root to sys.path so package imports resolve seamlessly
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.config import APP_TITLE
from app.seed import seed_database
from app.ui.styles import MAIN_STYLESHEET
from app.ui.main_window import MainWindow

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SmartBusApp")


def main():
    logger.info("Initializing Smart Bus Reservation System...")

    # Ensure database schema is created and populated with demo seed data
    try:
        seed_database()
        logger.info("Database initialized and verified.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        sys.exit(1)

    # Initialize Qt Desktop Application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    
    # Apply modern custom stylesheet
    app.setStyleSheet(MAIN_STYLESHEET)

    # Launch Main Window
    window = MainWindow()
    window.show()

    logger.info("Application launched successfully.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
