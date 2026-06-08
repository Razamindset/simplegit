from pathlib import Path
import shutil


class FileManager:
    """Handles copying, restoring, and clearing project files."""

    SIMPLEGIT_DIR = ".simplegit"

    def load_ignore_rules(self, project_dir):
        """Read ignore rules from .simplegit/ignore.txt."""
        ignore_file = Path(project_dir) / self.SIMPLEGIT_DIR / "ignore.txt"

        if not ignore_file.exists():
            return set()

        rules = set()

        with open(ignore_file, "r") as file:
            for line in file:
                rule = line.strip().strip("/\\")

                if rule and not rule.startswith("#"):
                    rules.add(rule)

        return rules

    def should_ignore(self, relative_path, ignore_rules):
        """Return True when a relative path matches a SimpleGit ignore rule."""
        parts = Path(relative_path).parts

        if self.SIMPLEGIT_DIR in parts:
            return True

        for rule in ignore_rules:
            rule_path = Path(rule)
            rule_parts = rule_path.parts

            if not rule_parts:
                continue

            if rule in parts:
                return True

            if parts[: len(rule_parts)] == rule_parts:
                return True

        return False

    def copy_project_files(self, project_dir, files_path):
        """
        Copy project files into a snapshot folder.

        The .simplegit folder and ignore.txt entries are skipped.
        """
        project_dir = Path(project_dir)
        files_path = Path(files_path)
        files_path.mkdir(parents=True, exist_ok=True)
        ignore_rules = self.load_ignore_rules(project_dir)

        for item in project_dir.rglob("*"):
            relative_path = item.relative_to(project_dir)

            if self.should_ignore(relative_path, ignore_rules):
                continue

            destination = files_path / relative_path

            if item.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            elif item.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, destination)

    def restore_files(self, snapshot_files, project_dir):
        """Restore files from a snapshot folder back into the project."""
        snapshot_files = Path(snapshot_files)
        project_dir = Path(project_dir)
        project_dir.mkdir(parents=True, exist_ok=True)
        ignore_rules = self.load_ignore_rules(project_dir)

        for item in snapshot_files.rglob("*"):
            relative_path = item.relative_to(snapshot_files)

            if self.should_ignore(relative_path, ignore_rules):
                continue

            destination = project_dir / relative_path

            if item.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            elif item.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, destination)

    def delete_working_files(self, project_dir):
        """
        Delete current project files before restoring a snapshot.

        The .simplegit folder is preserved because it stores repository data.
        """
        project_dir = Path(project_dir)
        ignore_rules = self.load_ignore_rules(project_dir)

        for item in project_dir.iterdir():
            relative_path = item.relative_to(project_dir)

            if self.should_ignore(relative_path, ignore_rules):
                continue

            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
