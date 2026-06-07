from pathlib import Path
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QColor, QPainter, QPen
    from PyQt6.QtWidgets import (
        QApplication,
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError as error:
    raise SystemExit("PyQt6 is required. Install it with: pip install PyQt6") from error

from core.file_manager import FileManager
from core.repository import Repository
from core.snapshot import SnapshotManager


class GraphMarker(QWidget):
    """Paints one node and the vertical connector line for the version graph."""

    MARKER_HEIGHT = 92

    def __init__(self, is_first=False, is_last=False, is_current=False):
        super().__init__()
        self.is_first = is_first
        self.is_last = is_last
        self.is_current = is_current
        self.setFixedWidth(72)
        self.setFixedHeight(self.MARKER_HEIGHT)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center_x = self.width() // 2
        center_y = self.height() // 2

        line_pen = QPen(QColor("#a7b4c2"), 2)
        painter.setPen(line_pen)

        if not self.is_first:
            painter.drawLine(center_x, 0, center_x, center_y - 13)

        if not self.is_last:
            painter.drawLine(center_x, center_y + 13, center_x, self.height())

        node_color = QColor("#2166d1") if self.is_current else QColor("#6b7d90")
        outer_color = QColor("#bfdbfe") if self.is_current else QColor("#e2e8f0")

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(outer_color)
        painter.drawEllipse(center_x - 14, center_y - 14, 28, 28)

        painter.setBrush(node_color)
        painter.drawEllipse(center_x - 8, center_y - 8, 16, 16)

        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.setBrush(node_color)
        painter.drawEllipse(center_x - 7, center_y - 7, 14, 14)


class VersionNode(QWidget):
    """One visible version row in the timeline graph."""

    switch_requested = pyqtSignal(str)

    def __init__(self, snapshot, is_first=False, is_last=False, is_current=False):
        super().__init__()
        self.snapshot = snapshot
        self.is_current = is_current

        self.setObjectName("VersionNodeCurrent" if is_current else "VersionNode")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(GraphMarker.MARKER_HEIGHT)

        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        row_layout.addWidget(GraphMarker(is_first, is_last, is_current))

        content = QWidget()
        content.setObjectName("VersionContent")
        content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 11, 16, 11)
        content_layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        title = QLabel(f"{snapshot.id}  {snapshot.message}")
        title.setObjectName("VersionTitle")

        badge = QLabel("Current" if is_current else "Saved")
        badge.setObjectName("CurrentBadge" if is_current else "PreviousBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        switch_button = QPushButton("Current" if is_current else "Switch")
        switch_button.setObjectName("SmallButton")
        switch_button.setEnabled(not is_current)
        switch_button.clicked.connect(self._request_switch)

        top_row.addWidget(title, stretch=1)
        top_row.addWidget(badge)
        top_row.addWidget(switch_button)

        details = QLabel(self._details_text())
        details.setObjectName("VersionDetails")

        content_layout.addLayout(top_row)
        content_layout.addWidget(details)

        row_layout.addWidget(content, stretch=1)

    def _details_text(self):
        text = snapshot_time = self.snapshot.timestamp

        if self.snapshot.parent:
            text = f"{snapshot_time}  |  parent: {self.snapshot.parent}"

        return text

    def _request_switch(self):
        self.switch_requested.emit(self.snapshot.id)


class VersionTimeline(QWidget):
    """Vertical node-to-node version graph with per-version switch buttons."""

    switch_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("TimelineCanvas")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 16, 18, 16)
        self.layout.setSpacing(0)

    def set_versions(self, snapshots, current_snapshot_id):
        self._clear()

        if not snapshots:
            empty = QLabel("No saved versions yet. Save your first version to start the history.")
            empty.setObjectName("EmptyTimeline")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setMinimumHeight(180)
            self.layout.addWidget(empty)
            self.layout.addStretch(1)
            return

        newest_first = list(reversed(snapshots))

        for index, snapshot in enumerate(newest_first):
            node = VersionNode(
                snapshot=snapshot,
                is_first=index == 0,
                is_last=index == len(newest_first) - 1,
                is_current=snapshot.id == current_snapshot_id,
            )
            node.switch_requested.connect(self.switch_requested.emit)
            self.layout.addWidget(node)

        self.layout.addStretch(1)

    def _clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()


class SimpleGitWindow(QMainWindow):
    """Guided GUI for choosing a project, saving versions, and switching versions."""

    def __init__(self):
        super().__init__()

        self.project_path = None
        self.repository = None
        self.file_manager = FileManager()
        self.snapshot_manager = None

        self.setWindowTitle("SimpleGit")
        self.resize(980, 680)

        self.views = QStackedWidget()
        self.setCentralWidget(self.views)

        self.start_view = self._build_start_view()
        self.unmanaged_view = self._build_unmanaged_project_view()
        self.managed_view = self._build_managed_project_view()

        self.views.addWidget(self.start_view)
        self.views.addWidget(self.unmanaged_view)
        self.views.addWidget(self.managed_view)

        self._apply_styles()
        self.show_start_view()

    def _build_start_view(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("SimpleGit")
        title.setObjectName("StartTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Select a folder to start managing project versions.")
        subtitle.setObjectName("StartSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        choose_button = QPushButton("Choose Project")
        choose_button.setObjectName("PrimaryLargeButton")
        choose_button.clicked.connect(self.choose_project)

        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(choose_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)

        return page

    def _build_unmanaged_project_view(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Start Managing This Project")
        title.setObjectName("PageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        message = QLabel("This folder is not managed by SimpleGit yet.")
        message.setObjectName("MutedText")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.unmanaged_path_label = QLabel("")
        self.unmanaged_path_label.setObjectName("PathText")
        self.unmanaged_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        start_button = QPushButton("Start Managing This Project")
        start_button.setObjectName("PrimaryButton")
        start_button.clicked.connect(self.start_managing_project)

        change_button = QPushButton("Choose Different Project")
        change_button.setObjectName("SecondaryButton")
        change_button.clicked.connect(self.choose_project)

        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(message)
        layout.addWidget(self.unmanaged_path_label)
        layout.addSpacing(10)
        layout.addWidget(start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(change_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)

        return page

    def _build_managed_project_view(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 22)
        layout.setSpacing(16)

        header = QHBoxLayout()
        header_text = QVBoxLayout()

        self.project_name_label = QLabel("Project")
        self.project_name_label.setObjectName("PageTitle")

        self.project_path_label = QLabel("")
        self.project_path_label.setObjectName("PathText")

        self.current_version_label = QLabel("Current version: none")
        self.current_version_label.setObjectName("MutedText")

        header_text.addWidget(self.project_name_label)
        header_text.addWidget(self.project_path_label)
        header_text.addWidget(self.current_version_label)

        change_button = QPushButton("Change Project")
        change_button.setObjectName("SecondaryButton")
        change_button.clicked.connect(self.choose_project)

        header.addLayout(header_text, stretch=1)
        header.addWidget(change_button, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        save_panel = QFrame()
        save_panel.setObjectName("Panel")
        save_layout = QHBoxLayout(save_panel)
        save_layout.setContentsMargins(16, 14, 16, 14)
        save_layout.setSpacing(10)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Short message for this version")

        save_button = QPushButton("Save Version")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.save_version)

        save_layout.addWidget(self.message_input, stretch=1)
        save_layout.addWidget(save_button)
        layout.addWidget(save_panel)

        history_title = QLabel("Version History")
        history_title.setObjectName("SectionTitle")
        layout.addWidget(history_title)

        self.version_timeline = VersionTimeline()
        self.version_timeline.switch_requested.connect(self.switch_to_version)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("TimelineScroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.viewport().setAutoFillBackground(True)
        scroll_area.viewport().setStyleSheet("background: #ffffff;")
        scroll_area.setWidget(self.version_timeline)
        layout.addWidget(scroll_area, stretch=1)

        self.status_label = QLabel("")
        self.status_label.setObjectName("StatusText")
        layout.addWidget(self.status_label)

        return page

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f5f7fa;
            }
            QLabel#StartTitle {
                color: #111827;
                font-size: 42px;
                font-weight: 800;
            }
            QLabel#StartSubtitle {
                color: #5f6b7a;
                font-size: 15px;
            }
            QLabel#PageTitle {
                color: #111827;
                font-size: 28px;
                font-weight: 800;
            }
            QLabel#SectionTitle {
                color: #1f2937;
                font-size: 16px;
                font-weight: 800;
                margin-top: 4px;
            }
            QLabel#MutedText,
            QLabel#StatusText {
                color: #607082;
                font-size: 13px;
            }
            QLabel#PathText {
                color: #435366;
                font-size: 13px;
            }
            QLabel#VersionTitle {
                color: #17202a;
                font-size: 14px;
                font-weight: 800;
            }
            QLabel#VersionDetails {
                color: #667382;
                font-size: 12px;
            }
            QLabel#CurrentBadge,
            QLabel#PreviousBadge {
                border-radius: 10px;
                font-size: 11px;
                font-weight: 700;
                padding: 4px 9px;
            }
            QLabel#CurrentBadge {
                background: #dbeafe;
                color: #1d4ed8;
            }
            QLabel#PreviousBadge {
                background: #eef2f7;
                color: #475569;
            }
            QLabel#EmptyTimeline {
                color: #7b8794;
                font-size: 14px;
            }
            QFrame#Panel,
            QWidget#TimelineCanvas {
                background: #ffffff;
                border: 1px solid #dbe2ea;
                border-radius: 8px;
            }
            QWidget#TimelineCanvas {
                border: none;
            }
            QWidget#VersionNode,
            QWidget#VersionNodeCurrent {
                background: transparent;
                border: none;
            }
            QWidget#VersionNodeCurrent {
                background: transparent;
            }
            QWidget#VersionContent {
                background: #ffffff;
                border: 1px solid #dbe2ea;
                border-radius: 8px;
            }
            QWidget#VersionNodeCurrent QWidget#VersionContent {
                background: #f8fbff;
                border: 1px solid #93c5fd;
            }
            QLineEdit {
                background: #ffffff;
                border: 1px solid #cfd8e3;
                border-radius: 7px;
                color: #17202a;
                padding: 10px 12px;
            }
            QPushButton {
                border-radius: 7px;
                font-weight: 700;
                padding: 10px 14px;
            }
            QPushButton#PrimaryLargeButton {
                background: #2166d1;
                border: 1px solid #1d5fc3;
                color: #ffffff;
                font-size: 18px;
                min-width: 230px;
                padding: 16px 22px;
            }
            QPushButton#PrimaryButton,
            QPushButton {
                background: #2166d1;
                border: 1px solid #1d5fc3;
                color: #ffffff;
            }
            QPushButton#SecondaryButton {
                background: #ffffff;
                border: 1px solid #cfd8e3;
                color: #304155;
            }
            QPushButton#SmallButton {
                min-width: 86px;
                padding: 7px 12px;
            }
            QPushButton:hover {
                background: #1d5fc3;
            }
            QPushButton#SecondaryButton:hover {
                background: #eef4fb;
            }
            QPushButton:disabled {
                background: #e5eaf0;
                border-color: #d8e0e8;
                color: #7b8794;
            }
            QScrollArea#TimelineScroll {
                background: #ffffff;
                border: 1px solid #dbe2ea;
                border-radius: 8px;
            }
            """
        )

    def show_start_view(self):
        self.views.setCurrentWidget(self.start_view)

    def choose_project(self):
        selected_folder = QFileDialog.getExistingDirectory(self, "Choose Project Folder")

        if not selected_folder:
            return

        self.project_path = Path(selected_folder)
        self.repository = Repository(self.project_path)
        self.snapshot_manager = SnapshotManager(self.repository.repo_path)
        self.show_project_state()

    def show_project_state(self):
        if self.repository.is_repository():
            self.show_managed_project_view()
        else:
            self.show_unmanaged_project_view()

    def show_unmanaged_project_view(self):
        self.unmanaged_path_label.setText(str(self.project_path))
        self.views.setCurrentWidget(self.unmanaged_view)

    def start_managing_project(self):
        if self.repository is None:
            self.show_start_view()
            return

        try:
            self.repository.initialize()
            self.show_managed_project_view()
            self.status_label.setText("Project is now managed by SimpleGit.")
        except Exception as error:
            QMessageBox.critical(self, "Could Not Start", str(error))

    def show_managed_project_view(self):
        self.project_name_label.setText(self.project_path.name)
        self.project_path_label.setText(str(self.project_path))
        self.views.setCurrentWidget(self.managed_view)
        self.refresh_versions()

    def save_version(self):
        if not self._has_managed_project():
            return

        message = self.message_input.text().strip()

        if not message:
            QMessageBox.warning(self, "Message Needed", "Write a short message for this version.")
            return

        try:
            snapshot = self.snapshot_manager.create_snapshot(
                message,
                self.repository.project_path,
                self.file_manager,
            )
            self.message_input.clear()
            self.refresh_versions()
            self.status_label.setText(f"Saved version {snapshot.id}.")
        except Exception as error:
            QMessageBox.critical(self, "Could Not Save Version", str(error))

    def switch_to_version(self, snapshot_id):
        if not self._has_managed_project():
            return

        current_snapshot = self._read_current_snapshot()
        if snapshot_id == current_snapshot:
            self.status_label.setText(f"{snapshot_id} is already the current version.")
            return

        response = QMessageBox.question(
            self,
            "Switch Version",
            f"Switch to {snapshot_id}? Current project files will be replaced.",
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
            self.refresh_versions()
            self.status_label.setText(f"Switched to version {snapshot.id}.")
        except Exception as error:
            QMessageBox.critical(self, "Could Not Switch Version", str(error))

    def refresh_versions(self):
        if not self._has_managed_project(show_message=False):
            return

        current_snapshot = self._read_current_snapshot()
        snapshots = self.snapshot_manager.get_all_snapshots()

        self.current_version_label.setText(f"Current version: {current_snapshot or 'none'}")
        self.version_timeline.set_versions(snapshots, current_snapshot)

        if not snapshots:
            self.status_label.setText("Save your first version when the project is ready.")

    def _read_current_snapshot(self):
        if self.repository is None or not self.repository.head_file.exists():
            return None

        try:
            with open(self.repository.head_file, "r") as file:
                data = json.load(file)
            return data.get("current_snapshot")
        except (json.JSONDecodeError, OSError):
            return None

    def _has_managed_project(self, show_message=True):
        is_ready = self.repository is not None and self.repository.is_repository()

        if not is_ready and show_message:
            QMessageBox.warning(self, "Choose Project", "Choose and start managing a project first.")

        return is_ready


def main():
    app = QApplication(sys.argv)
    window = SimpleGitWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
