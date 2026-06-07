from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from pathlib import Path
import json 

@dataclass
class Snapshot:
    """Represents a single snapshot in the repository."""

    id: str
    message:str
    timestamp: str
    parent: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert snapshot to dictionary for JSON storage."""
        return {
            "id": self.id,
            "message": self.message,
            "timestamp": self.timestamp,
            "parent": self.parent
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Snapshot':
        return Snapshot(
            id=data["id"],
            message=data["message"],
            timestamp=data["timestamp"],
            parent=data.get("parent")
        )

class SnapshotManager:
    """Manages snapshot creation, restoration, and metadata."""

    def __init__(self, repo_path):
        """
        repo_path is the path to the .simplegit folder.

        Example:
            SnapshotManager("MyProject/.simplegit")
        """
        self.repo_path = Path(repo_path)
        self.snapshots_dir = self.repo_path / "snapshots"
        self.head_file = self.repo_path / "HEAD.json"


    def create_snapshot(
        self,
        message: str,
        project_dir: Path,
        file_manager
        )-> Snapshot:
        """
        Create a new snapshot.
        
        Args:
            message: Snapshot description
            project_dir: Path to project directory
            file_manager: FileManager instance for copying files
            
        Returns:
            Created Snapshot object
        """
        # Overall snapshot flow:
        # 1. Make sure the required .simplegit files/folders exist.
        # 2. Generate the next snapshot ID, such as s1 or s2.
        # 3. Copy the current project files into the snapshot folder.
        # 4. Save snapshot metadata in meta.json.
        # 5. Move HEAD.json to point to the new snapshot.
        self._ensure_repository_files()

        snapshot_id = self._generate_snap_id()
        parent_snapshot = self._get_current_snapshot()
        parent_id = parent_snapshot.id if parent_snapshot else None

        # Create snapshot directory
        snapshot_path = self.snapshots_dir / snapshot_id
        snapshot_path.mkdir(parents=True, exist_ok=True)

        files_path = snapshot_path / "files"
        files_path.mkdir(exist_ok=True)

        file_manager.copy_project_files(project_dir, files_path)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        snapshot = Snapshot(
            id=snapshot_id,
            message=message,
            timestamp=timestamp,
            parent=parent_id
        )
        
        # Save metadata
        self._save_snapshot_metadata(snapshot)
        
        # Update HEAD
        self._update_head(snapshot_id)
        
        return snapshot

    def restore_snapshot(self, snapshot_id: str, project_dir: Path, file_manager) -> Snapshot:
        """
        Restore a snapshot into the project directory.

        Current working files are deleted first, but .simplegit is preserved by
        FileManager.delete_working_files().
        """
        snapshot = self.get_snapshot(snapshot_id)

        if snapshot is None:
            raise FileNotFoundError(f"Snapshot '{snapshot_id}' was not found.")

        snapshot_files = self.snapshots_dir / snapshot_id / "files"

        if not snapshot_files.exists():
            raise FileNotFoundError(f"Files for snapshot '{snapshot_id}' were not found.")

        file_manager.delete_working_files(project_dir)
        file_manager.restore_files(snapshot_files, project_dir)
        self._update_head(snapshot_id)

        return snapshot

    def get_snapshot(self, snapshot_id: Optional[str]) -> Optional[Snapshot]:
        """Load one snapshot by ID."""
        if not snapshot_id:
            return None

        metadata_file = self.snapshots_dir / snapshot_id / "meta.json"

        if not metadata_file.exists():
            return None

        with open(metadata_file, "r") as f:
            data = json.load(f)

        return Snapshot.from_dict(data)

    def _update_head(self, snapshot_id: str) -> None:
        """Update HEAD to point to snapshot."""
        head_data = {"current_snapshot": snapshot_id}
        
        with open(self.head_file, "w") as f:
            json.dump(head_data, f, indent=2)


    def _save_snapshot_metadata(self, snapshot: Snapshot) -> None:
        """Save snapshot metadata to file."""
        snapshot_path = self.snapshots_dir / snapshot.id
        metadata_file = snapshot_path / "meta.json"
        
        with open(metadata_file, "w") as f:
            json.dump(snapshot.to_dict(), f, indent=2)


    def _get_current_snapshot(self) ->  Optional[Snapshot]:
        """Get currently checked out snapshot."""
        if not self.head_file.exists():
            return None
        
        try:
            with open(self.head_file, "r") as f:
                data = json.load(f)
            snapshot_id = data.get("current_snapshot")
            return self.get_snapshot(snapshot_id) if snapshot_id else None
        except (json.JSONDecodeError, KeyError):
            return None
        

    def get_all_snapshots(self) -> list[Snapshot]:
        snapshots = []

        if not self.snapshots_dir.exists():
            return snapshots
        
        for snapshot_dir in sorted(self.snapshots_dir.iterdir()):
            if snapshot_dir.is_dir():
                snapshot = self.get_snapshot(snapshot_dir.name)
                if snapshot:
                    snapshots.append(snapshot)

        return snapshots
    

    def _generate_snap_id(self) -> str:
        snapshots = self.get_all_snapshots()
        largest_number = 0

        for snapshot in snapshots:
            if snapshot.id.startswith("s") and snapshot.id[1:].isdigit():
                largest_number = max(largest_number, int(snapshot.id[1:]))
            elif snapshot.id.isdigit():
                largest_number = max(largest_number, int(snapshot.id))

        return f"s{largest_number + 1}"

    def _ensure_repository_files(self) -> None:
        """
        Prepare the repository files needed by snapshot creation.

        This method is called at the start of create_snapshot(). In the normal
        flow, Repository.initialize() already creates these files, but this
        check makes SnapshotManager safer if a folder is missing or the class is
        used directly in a test.

        It only creates:
        - .simplegit/snapshots/
        - .simplegit/HEAD.json
        """
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        if not self.head_file.exists():
            # HEAD tracks which snapshot is currently active.
            with open(self.head_file, "w") as f:
                json.dump({"current_snapshot": None}, f, indent=2)

    
