from pathlib import Path
import shutil
class FileManager:
    def __init__(self):
        pass
    
    def copy_project_files(self, project_dir, files_path):
        project_dir= Path(project_dir)
        files_path=Path(files_path)
        files_path.mkdir(parents=True,exist_ok=True)
    
        for item in project_dir.rglob("*"):
            if ".simplegit" in item.parts:
             continue
    
        relative_path=item.relative_to(project_dir)
        destination=files_path/relative_path
        
        
        if item.is_dir():
         destination.mkdir(
                parents=True,
                exist_ok=True
                )
        elif item.is_file():
         destination.parent.mkdir (
                parents=True,
                exist_ok=True
               )
        shutil.copy2(
        item,
        destination
        )
        
            
    def restore_files(self,snapshot_files,project_dir):
        snapshot_files=Path(snapshot_files)
        project_dir=Path(project_dir)
        
        for item in snapshot_files.rglob("*"):
            relative_path=item.relative_to(snapshot_files)
            destination=project_dir/relative_path
            if item.is_dir():
                
             destination.mkdir(
                    parents=True,
                    exist_ok=True
                )

            elif item.is_file():

             destination.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

            shutil.copy2(
                    item,
                    destination
                )

    

    def delete_working_files(self,project_dir):
        project_dir=Path(project_dir)
        for item in project_dir().iterdir():
            
            if item.name ==".simplegit":
                continue
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
    


