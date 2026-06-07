# File: file_manager.py

## Purpose

The `FileManager` class handles all file operations in SimpleGit.

Responsibilities:

* Copy project files into snapshots
* Restore snapshot files back into the project
* Delete current project files before restoration
* Protect `.simplegit` from being copied or deleted



# Class Creation


class FileManager:


Purpose:

Creates a class that groups all file handling functions together.

---

# Constant Variable

```python
SIMPLEGIT_DIR = ".simplegit"
```

Purpose:

Stores the repository folder name.

Why use it?

Instead of writing:

```python
".simplegit"
```

many times, we store it once and reuse it.

---

# Function 1

```python
copy_project_files(project_dir, files_path)
```

Purpose:

Copies project files into snapshot folders.

Example:

Current project:

```txt
Project/
    main.py
    app.py
    notes.txt
    .simplegit/
```

Snapshot destination:

```txt
.simplegit/snapshots/s1/files/
```

After execution:

```txt
.simplegit/snapshots/s1/files/
    main.py
    app.py
    notes.txt
```

`.simplegit` is skipped.

---

# Execution Flow

Step 1:

Function gets called

```python
file_manager.copy_project_files(
    project_dir,
    snapshot_folder
)
```

↓

Step 2:

Convert paths into Path objects

```python
project_dir = Path(project_dir)
files_path = Path(files_path)
```

Purpose:

Allows use of path methods like:

```python
rglob()
mkdir()
is_file()
```

↓

Step 3:

Create destination folder if missing

```python
files_path.mkdir(
parents=True,
exist_ok=True
)
```

Meaning:

parents=True

→ Create parent folders automatically

exist_ok=True

→ Don't give error if folder exists

↓

Step 4:

Search all files and folders

```python
for item in project_dir.rglob("*")
```

Purpose:

Recursively searches:

```txt
Project/
    main.py
    folder/
        app.py
```

Finds:

* main.py
* folder
* app.py

↓

Step 5:

Get relative path

```python
relative_path=item.relative_to(project_dir)
```

Example:

Full path:

```txt
C:/Project/folder/app.py
```

Becomes:

```txt
folder/app.py
```

↓

Step 6:

Check for .simplegit

```python
if self.SIMPLEGIT_DIR in relative_path.parts:
    continue
```

Purpose:

Skip repository folder.

Reason:

Otherwise snapshots copy themselves infinitely.

↓

Step 7:

Create destination

```python
destination=files_path/relative_path
```

Example:

```txt
.simplegit/snapshots/s1/files/folder/app.py
```

↓

Step 8:

If folder:

```python
destination.mkdir()
```

↓

Step 9:

If file:

```python
shutil.copy2()
```

Purpose:

Copies file with metadata.

---

# Function Call Chain

```txt
Snapshot button clicked
        ↓
create_snapshot()
        ↓
copy_project_files()
        ↓
rglob()
        ↓
copy2()
```

---

# Function 2

```python
restore_files(snapshot_files,project_dir)
```

Purpose:

Restores snapshot files back to project.

---

# Execution Flow

Step 1:

Function called

```python
restore_files(
snapshot_folder,
project_folder
)
```

↓

Step 2:

Convert paths

↓

Step 3:

Create project folder if needed

↓

Step 4:

Read snapshot files

```python
rglob("*")
```

↓

Step 5:

Skip .simplegit

↓

Step 6:

Build destination path

↓

Step 7:

Copy files

```python
shutil.copy2()
```

---

# Function Call Chain

```txt
Backward button clicked
        ↓
move_backward()
        ↓
restore_snapshot()
        ↓
restore_files()
        ↓
copy2()
```

---

# Function 3

```python
delete_working_files(project_dir)
```

Purpose:

Deletes current files before restoring snapshots.

---

# Example

Before:

```txt
Project/
    main.py
    app.py
    test.py
    .simplegit/
```

After:

```txt
Project/
    .simplegit/
```

Only repository data remains.

---

# Execution Flow

Step 1:

Function called

```python
delete_working_files(project_dir)
```

↓

Step 2:

Loop through project items


for item in project_dir.iterdir()
```

↓

Step 3:

Check:

if item.name==".simplegit"


↓

Step 4:

Skip repository folder

↓

Step 5:

If file:

```python
item.unlink()
```

Purpose:

Delete file

↓

Step 6:

If folder:

shutil.rmtree()

Purpose:

Delete folder completely


# Function Call Chain

```txt
Backward button clicked
        ↓
move_backward()
        ↓
restore_snapshot()
        ↓
delete_working_files()
        ↓
restore_files()

# Complete File Flow

User clicks Snapshot
        ↓
create_snapshot()
        ↓
copy_project_files()
        ↓
snapshot created


User clicks Backward
        ↓
move_backward()
        ↓
restore_snapshot()
        ↓
delete_working_files()
        ↓
restore_files()


User clicks Forward
        ↓
move_forward()
        ↓
restore_snapshot()
        ↓
delete_working_files()
        ↓
restore_files()






# File: repository.py

# Purpose

The `Repository` class is the main controller of SimpleGit.

Responsibilities:

* Initialize repository structure
* Check if repository exists
* Load repository information
* Create configuration files
* Create required folders

Think of it like:

```txt
Repository
     ↓
Controls
     ↓
Snapshots
Timeline
HEAD
Configuration
Ignore rules
```

---

# Class Creation

```python
class Repository:
```

Purpose:

Creates a class to manage the entire repository system.

---

# Constant Variable

```python
SIMPLEGIT_DIR=".simplegit"
```

Purpose:

Stores repository folder name.

Instead of writing:

```python
".simplegit"
```

many times, we save it once.

---

# Constructor

```python
def __init__(self,project_path):
```

Purpose:

Runs automatically whenever an object is created.

Example:

```python
project=Repository("MyProject")
```

Python automatically executes:

```python
__init__()
```

---

# Step-by-step Constructor Flow

Step 1:

Receive project path

```python
project_path="MyProject"
```

↓

Step 2:

Convert into Path object

```python
self.project_path=Path(project_path)
```

Purpose:

Allows use of path methods.

Example:

```python
exists()
mkdir()
```

↓

Step 3:

Create repository path

```python
self.repo_path=self.project_path/self.SIMPLEGIT_DIR
```

Example:

Before:

```txt
MyProject
```

After:

```txt
MyProject/.simplegit
```

↓

Step 4:

Create snapshot path

```python
self.snapshots_path=self.repo_path/"snapshots"
```

Result:

```txt
MyProject/.simplegit/snapshots
```

↓

Step 5:

Create timeline path

```python
self.timeline_path=self.repo_path/"timeline"
```

↓

Step 6:

Store important file locations

```python
self.head_file
self.config_file
self.ignore_file
```

Result:

```txt
MyProject/.simplegit/

HEAD.json
config.json
ignore.txt
```

---

# Constructor Flow Diagram

```txt
Repository("MyProject")
        ↓
__init__()
        ↓
Create project path
        ↓
Create repository path
        ↓
Create snapshots path
        ↓
Create timeline path
        ↓
Store file paths
```

---

# Function 1

```python
is_repository()
```

Purpose:

Checks whether `.simplegit` exists.

---

# Execution Flow

Step 1:

Function called

```python
project.is_repository()
```

↓

Step 2:

Check:

```python
self.repo_path.exists()
```

↓

Step 3:

Return result

If exists:

```python
True
```

If missing:

```python
False
```

---

# Function Flow

```txt
is_repository()
        ↓
repo_path.exists()
        ↓
Return True/False
```

---

# Function 2

```python
initialize()
```

Purpose:

Creates complete repository structure.

---

# Folder structure created

```txt
MyProject/

    .simplegit/
            |
            ├── snapshots/
            │
            ├── timeline/
            │
            ├── HEAD.json
            │
            ├── config.json
            │
            └── ignore.txt
```

---

# Execution Flow

Step 1:

Function called

```python
project.initialize()
```

↓

Step 2:

Check repository existence

```python
if self.is_repository()
```

If already exists:

```python
print(
"Repository already initialized."
)
```

Stop execution.

↓

Step 3:

Create folders

```python
self.repo_path.mkdir()

self.snapshots_path.mkdir()

self.timeline_path.mkdir()
```

Creates:

```txt
.simplegit
snapshots
timeline
```

↓

Step 4:

Create HEAD data

```python
head_data={
"current_snapshot":None
}
```

Purpose:

No snapshot exists yet.

↓

Step 5:

Write into:

```python
HEAD.json
```

Result:

```json
{
"current_snapshot":null
}
```

↓

Step 6:

Create config data

```python
config_data={
"repo_name":
self.project_path.name,

"created_at":
str(datetime.now())
}
```

Result:

```json
{
"repo_name":"MyProject",
"created_at":"2026-06-07"
}
```

↓

Step 7:

Save configuration

```python
json.dump()
```

↓

Step 8:

Create timeline

```python
timeline_data={
"timeline_name":"main",
"snapshots":[]
}
```

Result:

```json
{
"timeline_name":"main",
"snapshots":[]
}
```

↓

Step 9:

Create ignore list

```python
default_ignore=[
"__pycache__",
".venv",
"dist",
"build"
]
```

↓

Step 10:

Write ignore.txt

Result:

```txt
__pycache__
.venv
dist
build
```

↓

Step 11:

Display success message

```python
print(
"SimpleGit repository initialized successfully."
)
```

---

# Function Call Chain

```txt
Open Application
        ↓
User selects project
        ↓
Repository(project)
        ↓
initialize()
        ↓
is_repository()
        ↓
Create folders
        ↓
Create JSON files
        ↓
Repository created
```

---

# Function 3

```python
load()
```

Purpose:

Loads repository information.

---

# Execution Flow

Step 1:

Function called

```python
project.load()
```

↓

Step 2:

Check repository

```python
if not self.is_repository()
```

If false:

```python
raise Exception(
"Not a SimpleGit repository"
)
```

↓

Step 3:

Open:

```python
config.json
```

↓

Step 4:

Read data

```python
json.load()
```

↓

Step 5:

Open:

```python
HEAD.json
```

↓

Step 6:

Read data

↓

Step 7:

Print repository information

```python
Repository Loaded
Repository Name
Created At
Current Snapshot
```

↓

Step 8:

Return dictionary

```python
return{
"config":config,
"head":head
}
```

---

# Function Call Chain

```txt
Open Application
        ↓
Select Project Folder
        ↓
load()
        ↓
is_repository()
        ↓
Read config.json
        ↓
Read HEAD.json
        ↓
Display information
```

---

# Main Program Flow

```python
if __name__=="__main__"
```

Purpose:

Runs only when file executes directly.

---

# Execution Sequence

```txt
Program starts
        ↓
project=Repository("MyProject")
        ↓
__init__()
        ↓
project.initialize()
        ↓
initialize()
        ↓
project.load()
        ↓
load()
```

---

# Complete Repository Flow

```txt
Application Starts
        ↓
Create Repository object
        ↓
Check repository exists
        ↓
Initialize repository
        ↓
Create folders
        ↓
Create JSON files
        ↓
Load repository
        ↓
Display information
```








# File: snapshot_manager.py

# Purpose

`SnapshotManager` manages all snapshot operations.

Responsibilities:

* Create snapshots
* Restore snapshots
* Read snapshot information
* Update HEAD
* Save metadata
* Generate snapshot IDs

Think of it like:

```txt
SnapshotManager
        ↓
Create Snapshot
Restore Snapshot
Read Snapshot
Update HEAD
Save Metadata
```

---

# Dataclass: Snapshot

```python
@dataclass
class Snapshot
```

Purpose:

Represents one snapshot object.

Example:

```python
snapshot=Snapshot(
id="s1",
message="Added GUI",
timestamp="2026-06-07 12:00",
parent=None
)
```

Object stored:

```txt
Snapshot
    id=s1
    message=Added GUI
    timestamp=2026-06-07
    parent=None
```

---

# Attributes

```python
id:str
message:str
timestamp:str
parent:Optional[str]
```

Meaning:

`id`

→ snapshot name

Example:

```txt
s1
s2
s3
```

`message`

→ user description

Example:

```txt
"Added login screen"
```

`timestamp`

→ date and time

`parent`

→ previous snapshot

Example:

```txt
s2 → parent=s1
```

---

# Function 1

```python
to_dict()
```

Purpose:

Convert object into dictionary.

---

Example:

Before:

```python
Snapshot(
id="s1",
message="Added GUI",
timestamp="12:00"
)
```

↓

After:

```python
{
"id":"s1",
"message":"Added GUI",
"timestamp":"12:00",
"parent":None
}
```

Purpose:

JSON cannot directly save objects.

---

# Function Flow

```txt
Snapshot object
        ↓
to_dict()
        ↓
Dictionary
        ↓
json.dump()
```

---

# Function 2

```python
from_dict()
```

Purpose:

Convert dictionary back into Snapshot object.

---

Flow:

```txt
JSON file
        ↓
json.load()
        ↓
Dictionary
        ↓
from_dict()
        ↓
Snapshot object
```

---

# Constructor

```python
def __init__(repo_path)
```

Purpose:

Stores repository locations.

---

Execution Flow

Step 1:

Receive:

```python
SnapshotManager(
"MyProject/.simplegit"
)
```

↓

Step 2:

Convert path

```python
self.repo_path=Path(repo_path)
```

↓

Step 3:

Create snapshot folder path

```python
self.snapshots_dir=
self.repo_path/"snapshots"
```

↓

Step 4:

Store HEAD file

```python
self.head_file=
self.repo_path/"HEAD.json"
```

---

# Constructor Flow

```txt
SnapshotManager()
        ↓
Create repo path
        ↓
Create snapshots path
        ↓
Create HEAD path
```

---

# Function 3

```python
create_snapshot()
```

Purpose:

Creates new snapshot.

---

# Full Snapshot Flow

```txt
User clicks Snapshot
        ↓
GUI receives message
        ↓
create_snapshot()
        ↓
_ensure_repository_files()
        ↓
_generate_snap_id()
        ↓
_get_current_snapshot()
        ↓
Create folders
        ↓
copy_project_files()
        ↓
Create Snapshot object
        ↓
_save_snapshot_metadata()
        ↓
_update_head()
        ↓
Return Snapshot
```

---

# Detailed Execution

Step 1:

Call function

```python
create_snapshot(
message,
project_dir,
file_manager
)
```

↓

Step 2:

Check required files

```python
_ensure_repository_files()
```

Purpose:

Make sure:

```txt
.simplegit/
snapshots/
HEAD.json
```

exist

↓

Step 3:

Generate new ID

```python
_generate_snap_id()
```

Result:

```txt
s1
```

or

```txt
s2
```

↓

Step 4:

Get current snapshot

```python
_get_current_snapshot()
```

Result:

```txt
parent=s1
```

↓

Step 5:

Create snapshot folder

```python
snapshot_path.mkdir()
```

Result:

```txt
.simplegit/

snapshots/

    s2/
```

↓

Step 6:

Create files folder

```python
files_path.mkdir()
```

Result:

```txt
s2/

    files/
```

↓

Step 7:

Copy project files

```python
file_manager.copy_project_files()
```

↓

Step 8:

Create timestamp

```python
datetime.now()
```

↓

Step 9:

Create Snapshot object

```python
Snapshot(
id=s2,
message=message,
timestamp=time,
parent=s1
)
```

↓

Step 10:

Save metadata

```python
_save_snapshot_metadata()
```

Creates:

```txt
meta.json
```

↓

Step 11:

Update HEAD

```python
_update_head()
```

Result:

```json
{
"current_snapshot":"s2"
}
```

↓

Step 12:

Return snapshot

---

# Function 4

```python
restore_snapshot()
```

Purpose:

Restores snapshot files.

---

Execution Flow

```txt
User clicks Backward
        ↓
restore_snapshot("s1")
        ↓
get_snapshot()
        ↓
delete_working_files()
        ↓
restore_files()
        ↓
_update_head()
```

---

Detailed Steps

Step 1:

Load snapshot

```python
get_snapshot()
```

↓

Step 2:

Check snapshot exists

↓

Step 3:

Delete current files

```python
file_manager.delete_working_files()
```

↓

Step 4:

Copy snapshot files

```python
restore_files()
```

↓

Step 5:

Update HEAD

---

# Function 5

```python
get_snapshot()
```

Purpose:

Loads one snapshot.

---

Flow

```txt
get_snapshot("s2")
        ↓
Find meta.json
        ↓
json.load()
        ↓
from_dict()
        ↓
Return Snapshot object
```

---

# Function 6

```python
_update_head()
```

Purpose:

Move HEAD to current snapshot.

---

Example

Before:

```json
{
"current_snapshot":"s1"
}
```

↓

After:

```json
{
"current_snapshot":"s2"
}
```

---

# Function 7

```python
_save_snapshot_metadata()
```

Purpose:

Store snapshot information.

Creates:

```txt
meta.json
```

Result:

```json
{
"id":"s2",
"message":"Added GUI",
"timestamp":"2026-06-07",
"parent":"s1"
}
```

---

# Function 8

```python
_get_current_snapshot()
```

Purpose:

Find active snapshot.

---

Flow

```txt
Read HEAD.json
        ↓
Get current_snapshot
        ↓
Load snapshot
        ↓
Return object
```

---

# Function 9

```python
get_all_snapshots()
```

Purpose:

Load all snapshots.

---

Flow

```txt
Open snapshots/
        ↓
Loop through folders
        ↓
get_snapshot()
        ↓
Store in list
        ↓
Return list
```

---

# Function 10

```python
_generate_snap_id()
```

Purpose:

Generate next ID.

---

Example:

Current:

```txt
s1
s2
s3
```

↓

Generated:

```txt
s4
```

---

Flow

```txt
get_all_snapshots()
        ↓
Find largest number
        ↓
+1
        ↓
Return new ID
```

---

# Function 11

```python
_ensure_repository_files()
```

Purpose:

Safety function.

Checks:

```txt
.simplegit/
snapshots/
HEAD.json
```

If missing:

Create automatically.

---

# Complete File Flow

```txt
Application Starts
        ↓
Create SnapshotManager
        ↓
User clicks Snapshot
        ↓
create_snapshot()
        ↓
Generate ID
        ↓
Copy files
        ↓
Save metadata
        ↓
Update HEAD
        ↓
Snapshot created


User clicks Restore
        ↓
restore_snapshot()
        ↓
Delete working files
        ↓
Restore snapshot
        ↓
Update HEAD
```


