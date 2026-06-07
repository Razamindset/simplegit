from pathlib import Path
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from PyQt6.QtCore import QSize, Qt, pyqtSignal
    from PyQt6.QtGui import QColor, QFont, QPainter, QPen
    from PyQt6.QtWidgets import (
        QApplication,
        QFileDialog,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError as error:
    raise SystemExit("PyQt6 is required. Install it with: pip install PyQt6") from error

from core.file_manager import FileManager
from core.repository import Repository
from core.snapshot import SnapshotManager


class TimelineGraphWidget(QWidget):
    """Clickable VS Code-like snapshot graph for the single snapshot history."""

    snapshot_selected = pyqtSignal(str)

    ROW_HEIGHT = 74
    TOP_PADDING = 18
    GRAPH_X = 34

    def __init__(self):
        super().__init__()
        self.snapshots = []
        self.current_snapshot_id = None
        self.selected_snapshot_id = None
        self.setMinimumHeight(240)

    def set_snapshots(self, snapshots, current_snapshot_id):
        previous_selection = self.selected_snapshot_id
        self.snapshots = list(reversed(snapshots))
        self.current_snapshot_id = current_snapshot_id

        snapshot_ids = [snapshot.id for snapshot in self.snapshots]
        if previous_selection in snapshot_ids:
            self.selected_snapshot_id = previous_selection
        elif current_snapshot_id in snapshot_ids:
            self.selected_snapshot_id = current_snapshot_id
        elif snapshot_ids:
            self.selected_snapshot_id = snapshot_ids[0]
        else:
            self.selected_snapshot_id = None

        self.setMinimumHeight(max(240, self.TOP_PADDING * 2 + len(self.snapshots) * self.ROW_HEIGHT))
        self.updateGeometry()
        self.update()

    def sizeHint(self):
        height = max(240, self.TOP_PADDING * 2 + len(self.snapshots) * self.ROW_HEIGHT)
        return QSize(760, height)

    def mousePressEvent(self, event):
        row = int((event.position().y() - self.TOP_PADDING) // self.ROW_HEIGHT)

        if 0 <= row < len(self.snapshots):
            self.selected_snapshot_id = self.snapshots[row].id
            self.snapshot_selected.emit(self.selected_snapshot_id)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))

        if not self.snapshots:
            painter.setPen(QColor("#7b8794"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No snapshots yet")
            return

        first_y = self._node_y(0)
        last_y = self._node_y(len(self.snapshots) - 1)

        if len(self.snapshots) > 1:
            painter.setPen(QPen(QColor("#8ca0b3"), 3))
            painter.drawLine(self.GRAPH_X, first_y, self.GRAPH_X, last_y)

        for row, snapshot in enumerate(self.snapshots):
            self._draw_snapshot_row(painter, row, snapshot)

    def _draw_snapshot_row(self, painter, row, snapshot):
        y = self._node_y(row)
        row_top = self.TOP_PADDING + row * self.ROW_HEIGHT
        is_current = snapshot.id == self.current_snapshot_id
        is_selected = snapshot.id == self.selected_snapshot_id

        if is_selected:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#edf4ff"))
            painter.drawRoundedRect(10, row_top + 4, self.width() - 20, self.ROW_HEIGHT - 8, 8, 8)

        node_color = QColor("#2166d1") if is_current else QColor("#6b7d90")
        if is_selected:
            node_color = QColor("#0f62fe")

        painter.setPen(QPen(QColor("#ffffff"), 3))
        painter.setBrush(node_color)
        painter.drawEllipse(self.GRAPH_X - 8, y - 8, 16, 16)

        text_x = self.GRAPH_X + 30

        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor("#17202a"))
        painter.drawText(text_x, y - 8, f"{snapshot.id}  {snapshot.message}")

        detail_font = QFont()
        detail_font.setPointSize(9)
        painter.setFont(detail_font)
        painter.setPen(QColor("#667382"))

        detail = snapshot.timestamp
        if snapshot.parent:
            detail += f"    parent: {snapshot.parent}"
        if is_current:
            detail += "    current"

        painter.drawText(text_x, y + 16, detail)

    def _node_y(self, row):
        return self.TOP_PADDING + row * self.ROW_HEIGHT + self.ROW_HEIGHT // 2


class SimpleGitWindow(QMainWindow):
    """Main GUI window for the current SimpleGit core features."""

    def __init__(self):
        super().__init__()

        self.project_path = None
        self.repository = None
        self.file_manager = FileManager()
        self.snapshot_manager = None

        self.setWindowTitle("SimpleGit")
        self.resize(960, 620)

        self._build_ui()
        self._apply_styles()
        self._set_actions_enabled(False)

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(20, 18, 20, 18)
        root_layout.setSpacing(14)

        title = QLabel("SimpleGit")
        title.setObjectName("Title")

        subtitle = QLabel("Create and restore project snapshots")
        subtitle.setObjectName("Subtitle")

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)

        root_layout.addWidget(self._build_project_box())
        root_layout.addWidget(self._build_snapshot_box(), stretch=1)

        self.status_label = QLabel("Open a project folder to begin.")
        self.status_label.setObjectName("Status")
        root_layout.addWidget(self.status_label)

    def _build_project_box(self):
        box = QGroupBox("Project")
        layout = QGridLayout(box)
        layout.setColumnStretch(1, 1)

        path_label = QLabel("Folder")
        self.project_path_input = QLineEdit()
        self.project_path_input.setReadOnly(True)
        self.project_path_input.setPlaceholderText("No project selected")

        self.open_button = QPushButton("Open Project")
        self.init_button = QPushButton("Initialize")
        self.refresh_button = QPushButton("Refresh")

        self.open_button.clicked.connect(self.open_project)
        self.init_button.clicked.connect(self.initialize_repository)
        self.refresh_button.clicked.connect(self.refresh_repository_view)

        layout.addWidget(path_label, 0, 0)
        layout.addWidget(self.project_path_input, 0, 1)
        layout.addWidget(self.open_button, 0, 2)
        layout.addWidget(self.init_button, 0, 3)
        layout.addWidget(self.refresh_button, 0, 4)

        self.current_snapshot_label = QLabel("Current snapshot: none")
        self.current_snapshot_label.setObjectName("MutedText")
        layout.addWidget(self.current_snapshot_label, 1, 1, 1, 4)

        return box

    def _build_snapshot_box(self):
        box = QGroupBox("Snapshots")
        layout = QVBoxLayout(box)

        create_row = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Snapshot message")

        self.create_button = QPushButton("Create Snapshot")
        self.restore_button = QPushButton("Restore Selected")

        self.create_button.clicked.connect(self.create_snapshot)
        self.restore_button.clicked.connect(self.restore_selected_snapshot)

        create_row.addWidget(self.message_input, stretch=1)
        create_row.addWidget(self.create_button)
        create_row.addWidget(self.restore_button)
        layout.addLayout(create_row)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        timeline_label = QLabel("Timeline")
        timeline_label.setObjectName("SectionLabel")
        layout.addWidget(timeline_label)

        self.timeline_graph = TimelineGraphWidget()
        self.timeline_graph.snapshot_selected.connect(self._on_snapshot_selected)

        timeline_scroll = QScrollArea()
        timeline_scroll.setWidgetResizable(True)
        timeline_scroll.setFrameShape(QFrame.Shape.NoFrame)
        timeline_scroll.setWidget(self.timeline_graph)

        layout.addWidget(timeline_scroll, stretch=1)

        return box

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f6f7f9;
            }
            QLabel#Title {
                color: #17202a;
                font-size: 28px;
                font-weight: 700;
            }
            QLabel#Subtitle {
                color: #5d6975;
                font-size: 13px;
                margin-bottom: 4px;
            }
            QLabel#Status,
            QLabel#MutedText {
                color: #5d6975;
            }
            QLabel#SectionLabel {
                color: #394653;
                font-size: 13px;
                font-weight: 700;
                margin-top: 6px;
            }
            QGroupBox {
                background: #ffffff;
                border: 1px solid #d9dee5;
                border-radius: 8px;
                color: #17202a;
                font-weight: 600;
                margin-top: 12px;
                padding: 14px 12px 12px 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QLineEdit {
                background: #ffffff;
                border: 1px solid #cfd6df;
                border-radius: 6px;
                padding: 8px 10px;
                color: #17202a;
            }
            QLineEdit:read-only {
                background: #f4f6f8;
                color: #45515e;
            }
            QPushButton {
                background: #2166d1;
                border: 1px solid #1c5dbf;
                border-radius: 6px;
                color: #ffffff;
                font-weight: 600;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background: #1c5dbf;
            }
            QPushButton:disabled {
                background: #d8dee6;
                border-color: #d8dee6;
                color: #7b8794;
            }
            QScrollArea {
                background: #ffffff;
                border: 1px solid #d9dee5;
                border-radius: 6px;
            }
            """
        )

    def open_project(self):
        selected_folder = QFileDialog.getExistingDirectory(self, "Open Project Folder")

        if not selected_folder:
            return

        self.project_path = Path(selected_folder)
        self.repository = Repository(self.project_path)
        self.snapshot_manager = SnapshotManager(self.repository.repo_path)
        self.project_path_input.setText(str(self.project_path))
        self.refresh_repository_view()

    def initialize_repository(self):
        if not self._has_project():
            return

        try:
            self.repository.initialize()
            self.refresh_repository_view()
            QMessageBox.information(self, "Repository", "SimpleGit repository is ready.")
        except Exception as error:
            QMessageBox.critical(self, "Initialize Failed", str(error))

    def create_snapshot(self):
        if not self._has_repository():
            return

        message = self.message_input.text().strip()
        if not message:
            QMessageBox.warning(self, "Missing Message", "Please enter a snapshot message.")
            return

        try:
            snapshot = self.snapshot_manager.create_snapshot(
                message,
                self.repository.project_path,
                self.file_manager,
            )
            self.message_input.clear()
            self.refresh_repository_view()
            self.status_label.setText(f"Created snapshot {snapshot.id}.")
        except Exception as error:
            QMessageBox.critical(self, "Snapshot Failed", str(error))

    def restore_selected_snapshot(self):
        if not self._has_repository():
            return

        snapshot_id = self._selected_snapshot_id()
        if snapshot_id is None:
            QMessageBox.warning(self, "No Snapshot Selected", "Please select a snapshot first.")
            return

        response = QMessageBox.question(
            self,
            "Restore Snapshot",
            f"Restore {snapshot_id}? Current project files will be replaced.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if response != QMessageBox.StandardButton.Yes:
            return

        try:
            snapshot = self.snapshot_manager.restore_snapshot(
                snapshot_id,
                self.repository.project_path,
                self.file_manager,
            )
            self.refresh_repository_view()
            self.status_label.setText(f"Restored snapshot {snapshot.id}.")
        except Exception as error:
            QMessageBox.critical(self, "Restore Failed", str(error))

    def refresh_repository_view(self):
        if not self._has_project(show_message=False):
            self._set_actions_enabled(False)
            return

        repository_exists = self.repository.is_repository()
        self.init_button.setEnabled(not repository_exists)
        self.refresh_button.setEnabled(repository_exists)
        self.create_button.setEnabled(repository_exists)
        self.restore_button.setEnabled(repository_exists)

        if not repository_exists:
            self.timeline_graph.set_snapshots([], None)
            self.current_snapshot_label.setText("Current snapshot: none")
            self.status_label.setText("Project selected. Initialize it to start using SimpleGit.")
            return

        current_snapshot = self._read_current_snapshot()
        self._load_snapshots_into_graph(current_snapshot)
        self.current_snapshot_label.setText(f"Current snapshot: {current_snapshot or 'none'}")
        self.status_label.setText("Repository loaded.")

    def _load_snapshots_into_graph(self, current_snapshot):
        snapshots = self.snapshot_manager.get_all_snapshots()
        self.timeline_graph.set_snapshots(snapshots, current_snapshot)

    def _read_current_snapshot(self):
        if not self.repository.head_file.exists():
            return None

        try:
            with open(self.repository.head_file, "r") as file:
                data = json.load(file)
            return data.get("current_snapshot")
        except (json.JSONDecodeError, OSError):
            return None

    def _selected_snapshot_id(self):
        return self.timeline_graph.selected_snapshot_id

    def _on_snapshot_selected(self, snapshot_id):
        self.status_label.setText(f"Selected snapshot {snapshot_id}.")

    def _has_project(self, show_message=True):
        has_project = self.repository is not None and self.project_path is not None

        if not has_project and show_message:
            QMessageBox.warning(self, "No Project", "Please open a project folder first.")

        return has_project

    def _has_repository(self):
        if not self._has_project():
            return False

        if not self.repository.is_repository():
            QMessageBox.warning(self, "Not Initialized", "Please initialize this project first.")
            return False

        return True

    def _set_actions_enabled(self, enabled):
        self.init_button.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)
        self.create_button.setEnabled(enabled)
        self.restore_button.setEnabled(enabled)


def main():
    app = QApplication(sys.argv)
    window = SimpleGitWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
