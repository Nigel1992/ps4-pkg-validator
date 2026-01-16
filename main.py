#!/usr/bin/env python3
"""PS4 PKG Validator - GUI Application."""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTextEdit, QListWidget,
    QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont

from pkg_parser import PKGParser


class PKGValidatorWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("PS4 PKG Validator")
        self.setGeometry(100, 100, 900, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel("Drop PS4 PKG Files Here")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        drop_zone_layout = QVBoxLayout()
        
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.currentItemChanged.connect(self.on_file_selected)
        drop_zone_layout.addWidget(QLabel("Files:"))
        drop_zone_layout.addWidget(self.file_list, stretch=1)
        
        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        self.info_display.setPlaceholderText("Select a file to view PKG information...")
        drop_zone_layout.addWidget(QLabel("PKG Information:"))
        drop_zone_layout.addWidget(self.info_display, stretch=2)
        
        main_layout.addLayout(drop_zone_layout)
        
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_files)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        
        self.about_button = QPushButton("About")
        self.about_button.clicked.connect(self.show_about)
        button_layout.addWidget(self.about_button)
        
        main_layout.addLayout(button_layout)
        
        self.setAcceptDrops(True)
        self.pkg_data = {}
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        mime_data = event.mimeData()
        
        if mime_data.hasUrls():
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                
                if file_path.lower().endswith('.pkg'):
                    self.process_pkg_file(file_path)
                else:
                    QMessageBox.warning(
                        self,
                        "Invalid File",
                        f"'{Path(file_path).name}' is not a .pkg file."
                    )
            
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def process_pkg_file(self, file_path: str):
        file_name = Path(file_path).name
        
        for i in range(self.file_list.count()):
            if self.file_list.item(i).data(Qt.ItemDataRole.UserRole) == file_path:
                QMessageBox.information(
                    self,
                    "Already Added",
                    f"'{file_name}' is already in the list."
                )
                return
        
        parser = PKGParser(file_path)
        is_valid = parser.validate()
        
        item = QListWidgetItem()
        if is_valid:
            item.setText(f"✓ {file_name}")
            item.setForeground(Qt.GlobalColor.darkGreen)
        else:
            item.setText(f"✗ {file_name}")
            item.setForeground(Qt.GlobalColor.red)
        
        item.setData(Qt.ItemDataRole.UserRole, file_path)
        self.file_list.addItem(item)
        
        self.pkg_data[file_path] = parser
        self.file_list.setCurrentItem(item)
    
    def on_file_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        if current is None:
            self.info_display.clear()
            return
        
        file_path = current.data(Qt.ItemDataRole.UserRole)
        parser = self.pkg_data.get(file_path)
        
        if parser is None:
            self.info_display.setText("Error: No parser data found.")
            return
        
        # Display info
        if parser.is_valid:
            info_text = f"<h3>✓ Valid PKG File</h3>"
            info_text += f"<p><b>File:</b> {Path(file_path).name}</p>"
            info_text += f"<p><b>Size:</b> {self._format_file_size(file_path)}</p>"
            info_text += "<hr>"
            
            if 'Title' in parser.info:
                info_text += f"<h4>{parser.info['Title']}</h4>"
            
            info_text += "<p><b>PKG Information:</b></p><ul>"
            for key in ['PKG Type', 'Category', 'PKG Flags', 'Content Type', 'Content Flags']:
                if key in parser.info:
                    info_text += f"<li><b>{key}:</b> {parser.info[key]}</li>"
            info_text += "</ul>"
            
            info_text += "<p><b>Identifiers:</b></p><ul>"
            for key in ['Content ID', 'Title ID']:
                if key in parser.info:
                    info_text += f"<li><b>{key}:</b> {parser.info[key]}</li>"
            info_text += "</ul>"
            
            info_text += "<p><b>Version / Firmware:</b></p><ul>"
            for key in ['App Version', 'Version', 'Minimum Firmware', 'SYSTEM_VER']:
                if key in parser.info:
                    label = key if key != 'SYSTEM_VER' else 'Raw SYSTEM_VER'
                    info_text += f"<li><b>{label}:</b> {parser.info[key]}</li>"
            info_text += "</ul>"

            info_text += "<p><b>Compatibility:</b></p><ul>"
            for key in ['Trophies Present', 'Backport']:
                if key in parser.info:
                    info_text += f"<li><b>{key}:</b> {parser.info[key]}</li>"
            info_text += "</ul>"
            
            info_text += "<p><b>File Structure:</b></p><ul>"
            for key in ['File Count', 'Entry Count', 'Body Offset', 'Body Size']:
                if key in parser.info:
                    info_text += f"<li><b>{key}:</b> {parser.info[key]}</li>"
            info_text += "</ul>"
        else:
            info_text = f"<h3>Invalid PKG File</h3>"
            info_text += f"<p><b>File:</b> {Path(file_path).name}</p>"
            info_text += f"<p><b>Error:</b> {parser.error_message}</p>"
        
        self.info_display.setHtml(info_text)
    
    def clear_files(self):
        if self.file_list.count() == 0:
            return
        
        reply = QMessageBox.question(
            self,
            "Clear All",
            "Are you sure you want to clear all files?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.file_list.clear()
            self.pkg_data.clear()
            self.info_display.clear()
    
    def show_about(self):
        QMessageBox.about(
            self,
            "About PS4 PKG Validator",
            "<h3>PS4 PKG Validator</h3>"
            "<p>A simple tool to validate PS4 PKG files by parsing their headers.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Drag and drop .pkg files</li>"
            "<li>Validate PKG magic and structure</li>"
            "<li>Extract Content ID, Title ID, and metadata</li>"
            "</ul>"
            "<p><b>Version:</b> 1.1.0</p>"
        )
    
    def _format_file_size(self, file_path: str) -> str:
        size = Path(file_path).stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("PS4 PKG Validator")
    
    window = PKGValidatorWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
