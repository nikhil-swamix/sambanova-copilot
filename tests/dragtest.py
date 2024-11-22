from PySide6.QtWidgets import QLabel, QWidget, QApplication, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag

class DraggableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setText("Drop files here!")
        # Allow styling 
        self.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 10px;
            }
            QLabel:hover {
                background-color: #e0e0e0;
                border-color: #999;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.position()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
            
        # Check if minimum drag distance is met
        if ((event.position() - self.drag_start_position).manhattanLength() 
                < QApplication.startDragDistance()):
            return

        # Create drag object
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.text())
        drag.setMimeData(mime_data)

        # Optional: Set drag pixmap/visual
        # pixmap = self.grab()
        # drag.setPixmap(pixmap)
        # drag.setHotSpot(event.position().toPoint())

        # Start drag operation
        drop_action = drag.exec_(Qt.CopyAction | Qt.MoveAction)
        
        if drop_action == Qt.MoveAction:
            # Handle successful move
            pass

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet("""
                QLabel {
                    background-color: #e0f0e0;
                    border: 2px dashed #4CAF50;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 10px;
            }
            QLabel:hover {
                background-color: #e0e0e0;
                border-color: #999;
            }
        """)
        event.accept()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                file_paths.append(url.toLocalFile())
            self.parent().update_file_list(file_paths)
            
        event.accept()
        
        # Reset style after drop
        self.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 10px;
            }
            QLabel:hover {
                background-color: #e0e0e0;
                border-color: #999;
            }
        """)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Drop Demo")
        self.setGeometry(100, 100, 400, 400)
        self.setAcceptDrops(True)
        
        # Create main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # Create drop zone
        self.drop_label = DraggableLabel(self)
        self.main_layout.addWidget(self.drop_label)
        
        # Container for dynamic labels
        self.dynamic_labels_container = QWidget()
        self.dynamic_layout = QVBoxLayout()
        self.dynamic_labels_container.setLayout(self.dynamic_layout)
        self.main_layout.addWidget(self.dynamic_labels_container)
        
        # Control buttons
        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Label")
        self.add_button.clicked.connect(self.add_dynamic_label)
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_dynamic_labels)
        
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.clear_button)
        self.main_layout.addLayout(self.button_layout)
        
        # Style the window
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
            QPushButton {
                padding: 5px 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
    def create_label_with_remove(self):
        # Create container widget for label and button
        container = QWidget()
        layout = QHBoxLayout()
        container.setLayout(layout)
        
        # Create label
        label = QLabel(f"Dynamic Label {self.dynamic_layout.count() + 1}")
        label.setStyleSheet("""
            QLabel {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 8px;
            }
        """)
        
        # Create remove button
        remove_button = QPushButton("×")
        remove_button.setFixedSize(20, 20)
        remove_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff0000;
            }
        """)
        
        # Connect remove button
        remove_button.clicked.connect(lambda: self.remove_dynamic_label(container))
        
        layout.addWidget(label)
        layout.addWidget(remove_button)
        return container
        
    def add_dynamic_label(self):
        label_container = self.create_label_with_remove()
        self.dynamic_layout.addWidget(label_container)
        
    def remove_dynamic_label(self, container):
        container.deleteLater()
        
    def clear_dynamic_labels(self):
        while self.dynamic_layout.count():
            item = self.dynamic_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def update_file_list(self, file_paths):
        # Create a new dynamic label for each dropped file
        for file_path in file_paths:
            label_container = QWidget()
            layout = QHBoxLayout()
            label_container.setLayout(layout)
            
            label = QLabel(file_path)
            label.setWordWrap(True)
            label.setStyleSheet("""
                QLabel {
                    background-color: #f8f8f8;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                    padding: 8px;
                }
            """)
            
            # Create remove button for file label
            remove_button = QPushButton("×")
            remove_button.setFixedSize(20, 20)
            remove_button.setStyleSheet("""
                QPushButton {
                    background-color: #ff4444;
                    color: white;
                    border-radius: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #ff0000;
                }
            """)
            remove_button.clicked.connect(lambda checked, w=label_container: self.remove_dynamic_label(w))
            
            layout.addWidget(label)
            layout.addWidget(remove_button)
            self.dynamic_layout.addWidget(label_container)

if __name__ == '__main__':
    import sys
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
