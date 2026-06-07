# How To Test SimpleGit

This guide explains how to test the current core code.

Right now, the working parts are:

- repository initialization
- repository loading
- file copying for snapshots
- snapshot creation
- snapshot metadata loading
- snapshot restore
- `HEAD.json` updates
- `.simplegit` safety during copy/delete/restore

The staging file is still a placeholder.

`gui/window.py` now has the first GUI implementation, but it requires PyQt6 to
be installed before it can run.

---

## 1. Open The Project Folder

In PowerShell, go to the project root:

```powershell
cd C:\Users\PMLS\Desktop\simplegit
```

---

## 2. Check Python Files Compile

Run:

```powershell
python -m py_compile core\repository.py core\file_manager.py core\snapshot.py core\staging.py gui\window.py
```

Expected result:

- no output
- no error message

If Python prints an error, read the file name and line number in the error.

---

## 3. Run The Full Core Smoke Test

Run this command from the project root:

```powershell
python -c "from pathlib import Path; import tempfile, json; from core.repository import Repository; from core.file_manager import FileManager; from core.snapshot import SnapshotManager; root=Path(tempfile.mkdtemp(prefix='simplegit-full-test-')); project=root/'project'; project.mkdir(); (project/'a.txt').write_text('version 1'); (project/'folder').mkdir(); (project/'folder'/'b.txt').write_text('nested file'); repo=Repository(project); assert not repo.is_repository(); repo.initialize(); assert repo.is_repository(); loaded=repo.load(); assert loaded['head']['current_snapshot'] is None; fm=FileManager(); sm=SnapshotManager(repo.repo_path); s1=sm.create_snapshot('first snapshot', project, fm); assert s1.id == 's1'; assert (repo.snapshots_path/'s1'/'files'/'a.txt').read_text() == 'version 1'; assert not (repo.snapshots_path/'s1'/'files'/'.simplegit').exists(); (project/'a.txt').write_text('version 2'); (project/'new.txt').write_text('new file'); s2=sm.create_snapshot('second snapshot', project, fm); assert s2.id == 's2'; assert sm.get_snapshot('s1').message == 'first snapshot'; sm.restore_snapshot('s1', project, fm); assert (project/'a.txt').read_text() == 'version 1'; assert not (project/'new.txt').exists(); assert (project/'.simplegit').exists(); head=json.loads(repo.head_file.read_text()); assert head['current_snapshot'] == 's1'; print('PASS full core test'); print('project', project); print('snapshots', sorted(p.name for p in repo.snapshots_path.iterdir())); print('head', head)"
```

Expected result:

```txt
PASS full core test
snapshots ['s1', 's2']
head {'current_snapshot': 's1'}
```

The exact temporary project path will be different on each computer.

---

## 4. What This Smoke Test Checks

The smoke test creates a temporary project and checks that:

- `.simplegit` does not exist before initialization
- `Repository.initialize()` creates the repository
- `Repository.load()` reads the repository data
- first snapshot becomes `s1`
- second snapshot becomes `s2`
- normal files are copied into snapshots
- `.simplegit` is not copied into snapshots
- snapshot metadata can be loaded
- restoring `s1` brings back the old file content
- files added after `s1` are removed during restore
- `.simplegit` is not deleted during restore
- `HEAD.json` points to the restored snapshot

---

## 5. Current Limitations

These are not bugs in the current test. They are unfinished parts of the project:

- `core/staging.py` is still only a placeholder.
- `gui/window.py` has the first GUI, but it still needs manual testing with PyQt6 installed.
- `Repository.initialize()` still creates `timeline/main.json`, but `SnapshotManager` does not currently use timeline logic.
- There is no backward/forward navigation method yet.
- There is no staging flow yet.

---

## 6. Run The GUI

First install PyQt6 if it is not already installed:

```powershell
pip install PyQt6
```

Then run:

```powershell
python gui\window.py
```

Manual GUI test:

1. Click `Choose Project`.
2. Select a small test folder, not this source-code folder.
3. If the folder is new to SimpleGit, click `Start Managing This Project`.
4. Type a short message for the version.
5. Click `Save Version`.
6. Change or add a file inside the test folder.
7. Save another version.
8. In the timeline graph, click `Switch to this version` on the first version.
9. Confirm the switch.

Expected result:

- the timeline graph shows `s1` and `s2`
- the current snapshot label updates
- switching to `s1` brings the test folder back to the first saved state
- the `.simplegit` folder remains inside the test folder

---

## 7. Rule For Teammates

Before pushing code, each teammate should run:

```powershell
python -m py_compile core\repository.py core\file_manager.py core\snapshot.py core\staging.py gui\window.py
```

Then they should run the full core smoke test above.

If both pass, the core code is at least safe for the current implemented features.
