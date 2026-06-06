from pathlib import Path
import json
from datetime import datetime


class Repository:
    """
    Main controller class for SimpleGit.

    functions:
    - initialize repository
    - load repository
    - check if repository exists
    """

    SIMPLEGIT_DIR = ".simplegit"

    def __init__(self, project_path):
        """
        project_path -> path of user project
        """

        self.project_path = Path(project_path)

        self.repo_path = self.project_path / self.SIMPLEGIT_DIR

        self.snapshots_path = self.repo_path / "snapshots"
        self.timeline_path = self.repo_path / "timeline"

        self.head_file = self.repo_path / "HEAD.json"
        self.config_file = self.repo_path / "config.json"
        self.ignore_file = self.repo_path / "ignore.txt"

    # CHECK REPOSITORY

    def is_repository(self):
        """
        Check if .simplegit folder exists.
        """

        return self.repo_path.exists()

    # INITIALIZE REPOSITORY

    def initialize(self):
        """
        Create complete repository structure.
        """

        # if repository already exists
        if self.is_repository():
            print("Repository already initialized.")
            return

        # create folders
        self.repo_path.mkdir()
        self.snapshots_path.mkdir()
        self.timeline_path.mkdir()
        head_data = {
            "current_snapshot": None
        }

        with open(self.head_file, "w") as file:
            json.dump(head_data, file, indent=4)
        config_data = {
            "repo_name": self.project_path.name,
            "created_at": str(datetime.now())
        }

        with open(self.config_file, "w") as file:
            json.dump(config_data, file, indent=4)
        timeline_data = {
            "timeline_name": "main",
            "snapshots": []
        }

        main_timeline = self.timeline_path / "main.json"

        with open(main_timeline, "w") as file:
            json.dump(timeline_data, file, indent=4)
        default_ignore = [
            "__pycache__",
            ".venv",
            "dist",
            "build"
        ]

        with open(self.ignore_file, "w") as file:
            for item in default_ignore:
                file.write(item + "\n")

        print("SimpleGit repository initialized successfully.")

    # LOAD REPOSITORY

    def load(self):
        """
        Load repository information.
        """

        if not self.is_repository():
            raise Exception("Not a SimpleGit repository.")
        with open(self.config_file, "r") as file:
            config = json.load(file)
        with open(self.head_file, "r") as file:
            head = json.load(file)

        print("Repository Loaded")
        print("-------------------")
        print(f"Repository Name : {config['repo_name']}")
        print(f"Created At      : {config['created_at']}")
        print(f"Current Snapshot: {head['current_snapshot']}")

        return {
            "config": config,
            "head": head
        }

# TESTING

if __name__ == "__main__":

    project = Repository("MyProject")
    project.initialize()
    project.load()