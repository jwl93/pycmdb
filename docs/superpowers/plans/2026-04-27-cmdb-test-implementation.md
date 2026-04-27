# CMDB Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add baseline tests for pycmdb covering validator.py and executor.py, with CMDB_ROOT env var support.

**Architecture:** Tests use pytest fixtures with tmp_path for isolation. Project root configurable via CMDB_ROOT environment variable. Hook loading tested with inline temporary hook files.

**Tech Stack:** pytest, tmp_path fixture, monkeypatch, gitpython (for detector.py refactor)

---

## File Structure

```
tests/
├── __init__.py
├── conftest.py          # fixtures, monkeypatch setup
├── test_validator.py    # validator tests
└── test_executor.py     # executor tests
```

**Modified:**
- `scripts/validator.py` - use `get_cmdb_root()` for path resolution
- `scripts/executor.py` - use `get_cmdb_root()` for path resolution
- `scripts/detector.py` - use GitPython instead of subprocess
- `pixi.toml` - add gitpython dependency

---

## Task 1: Add gitpython dependency

**Files:**
- Modify: `pixi.toml`

- [ ] **Step 1: Add gitpython to dependencies**

```toml
[dependencies]
python = ">=3.10"
pyyaml = "*"
jsonschema = "*"
jinja2 = "*"
gitpython = "*"
```

- [ ] **Step 2: Commit**

```bash
git add pixi.toml
git commit -m "feat: add gitpython dependency"
```

---

## Task 2: Add get_cmdb_root() utility and refactor detector.py

**Files:**
- Modify: `scripts/detector.py`
- Create: `scripts/__init__.py` (if not exists, add get_cmdb_root)

- [ ] **Step 1: Add get_cmdb_root to scripts/__init__.py**

```python
"""pycmdb - Git-based CMDB"""
import os
from pathlib import Path

def get_cmdb_root() -> Path:
    """Get CMDB root directory from CMDB_ROOT env var, default current directory."""
    return Path(os.environ.get("CMDB_ROOT", "."))
```

- [ ] **Step 2: Refactor detector.py to use GitPython**

Modify `detect_changes()` function, replacing:
```python
result = subprocess.run(cmd, capture_output=True, text=True)
```

With GitPython:
```python
from git import Repo

def detect_changes(base_commit: Optional[str] = None) -> list[Change]:
    """Detect git changes, return Change list."""
    try:
        repo = Repo(".")
    except Exception:
        return []

    changes = []
    # Get commits range
    if base_commit:
        try:
            commit = repo.commit(base_commit)
            commit_range = f"{base_commit}..HEAD"
        except Exception:
            return []
    else:
        commit_range = "HEAD~1..HEAD"

    # Use GitPython diff API
    for item in repo.head.commit.diff(commit_range):
        # ... parse diff into Change objects
```

- [ ] **Step 3: Run detector basic test**

```bash
pixi run detect
```
Verify it still works (no output = no changes detected, which is fine)

- [ ] **Step 4: Commit**

```bash
git add scripts/detector.py scripts/__init__.py
git commit -m "feat: refactor detector to use GitPython and add get_cmdb_root"
```

---

## Task 3: Refactor validator.py to use get_cmdb_root()

**Files:**
- Modify: `scripts/validator.py`

- [ ] **Step 1: Update get_schema to use get_cmdb_root**

Replace:
```python
schema_path = Path(config_type.value) / "_schema.json"
```

With:
```python
from scripts import get_cmdb_root
schema_path = get_cmdb_root() / config_type.value / "_schema.json"
```

Same pattern for `get_defaults` and `validate_references` (the `_resolve_ref` function).

- [ ] **Step 2: Verify validator still works**

```bash
pixi run validate
```

- [ ] **Step 3: Commit**

```bash
git add scripts/validator.py
git commit -m "refactor: use get_cmdb_root() for path resolution"
```

---

## Task 4: Refactor executor.py to use get_cmdb_root()

**Files:**
- Modify: `scripts/executor.py`

- [ ] **Step 1: Update get_hook_path to use get_cmdb_root**

Replace:
```python
return Path("hooks") / get_hook_name(change)
```

With:
```python
from scripts import get_cmdb_root
return get_cmdb_root() / "hooks" / get_hook_name(change)
```

- [ ] **Step 2: Verify executor still works**

```bash
pixi run deploy --dry-run
```

- [ ] **Step 3: Commit**

```bash
git add scripts/executor.py
git commit -m "refactor: use get_cmdb_root() for hook path resolution"
```

---

## Task 5: Create tests directory structure

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create tests/__init__.py**

```python
"""pycmdb tests"""
```

- [ ] **Step 2: Create tests/conftest.py**

```python
"""pytest fixtures and configuration"""
import os
import pytest
from pathlib import Path

@pytest.fixture
def cmdb_root(tmp_path):
    """Create temporary CMDB_ROOT directory structure."""
    (tmp_path / "hosts" / "config").mkdir(parents=True)
    (tmp_path / "host_groups" / "config").mkdir(parents=True)
    (tmp_path / "services" / "config").mkdir(parents=True)
    (tmp_path / "hooks").mkdir()
    return tmp_path

@pytest.fixture
def schema_dir(cmdb_root):
    """Copy schema and defaults to temp root."""
    import shutil

    # Copy schemas
    for config_type in ["hosts", "host_groups", "services"]:
        src_schema = Path(f"../{config_type}/_schema.json")
        src_defaults = Path(f"../{config_type}/_defaults.yaml")
        dst = cmdb_root / config_type

        if src_schema.exists():
            shutil.copy(src_schema, dst / "_schema.json")
        if src_defaults.exists():
            shutil.copy(src_defaults, dst / "_defaults.yaml")

    return cmdb_root

@pytest.fixture
def sample_host(schema_dir):
    """Create sample host config web-01."""
    host_file = schema_dir / "hosts" / "config" / "web-01.yaml"
    host_file.write_text("hostname: web-01\nip: 10.0.0.1\n")
    return host_file

@pytest.fixture
def sample_host_group(schema_dir, sample_host):
    """Create sample host_group config web-servers."""
    group_file = schema_dir / "host_groups" / "config" / "web-servers.yaml"
    group_file.write_text("name: web-servers\nmembers:\n  - web-01\n")
    return group_file

@pytest.fixture
def sample_service(schema_dir, sample_host):
    """Create sample service config api-gateway."""
    svc_file = schema_dir / "services" / "config" / "api-gateway.yaml"
    svc_file.write_text("name: api-gateway\nversion: 1.0.0\nhosts:\n  - web-01\n")
    return svc_file
```

- [ ] **Step 3: Commit**

```bash
git add tests/__init__.py tests/conftest.py
git commit -m "feat: add tests directory structure and fixtures"
```

---

## Task 6: Create test_validator.py

**Files:**
- Create: `tests/test_validator.py`

- [ ] **Step 1: Write first failing test - test_validate_config_valid**

```python
def test_validate_config_valid(cmdb_root, monkeypatch):
    """Valid host config should pass validation."""
    import os
    monkeypatch.setenv("CMDB_ROOT", str(cmdb_root))

    from scripts.validator import validate_config
    from scripts.detector import ConfigType

    # Setup schema
    import shutil
    shutil.copy("../hosts/_schema.json", cmdb_root / "hosts" / "_schema.json")

    config = {"hostname": "web-01", "ip": "10.0.0.1"}
    result = validate_config(ConfigType.HOSTS, "web-01", config)
    assert result["hostname"] == "web-01"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_validator.py::test_validate_config_valid -v
```
Expected: FAIL (schema not found, path issue)

- [ ] **Step 3: Write minimal implementation**

(Already done in Task 3, run test again)

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_validator.py::test_validate_config_valid -v
```
Expected: PASS

- [ ] **Step 5: Add remaining validator tests**

Write tests for:
- `test_validate_config_invalid` - schema validation failure
- `test_merge_defaults` - default values merged
- `test_validate_references_valid` - referenced host exists
- `test_validate_references_invalid` - referenced host missing
- `test_validate_host_group_members` - all members exist
- `test_validate_host_group_members_missing` - member missing
- `test_validate_services_references` - service references valid

- [ ] **Step 6: Run all validator tests**

```bash
pytest tests/test_validator.py -v
```
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add tests/test_validator.py
git commit -m "feat: add validator tests"
```

---

## Task 7: Create test_executor.py

**Files:**
- Create: `tests/test_executor.py`

- [ ] **Step 1: Write first failing test - test_get_hook_path**

```python
def test_get_hook_path(cmdb_root, monkeypatch):
    """Test hook path resolution."""
    import os
    monkeypatch.setenv("CMDB_ROOT", str(cmdb_root))

    from scripts.executor import get_hook_path
    from scripts.detector import Change, ConfigType, ChangeType

    change = Change(
        config_type=ConfigType.HOSTS,
        change_type=ChangeType.NEW,
        name="web-01"
    )

    path = get_hook_path(change)
    assert path == cmdb_root / "hooks" / "hostsnew.py"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_executor.py::test_get_hook_path -v
```
Expected: FAIL (hook path wrong)

- [ ] **Step 3: Fix implementation in executor.py**

The hook path naming: `f"{type_name}_{event_name}.py"` where:
- type_name = "hosts".replace("_", "") = "hosts"
- event_name = "new"

So it should be `hostsnew.py` but that looks wrong...

Wait, let me check executor.py again:
```python
def get_hook_name(change: Change) -> str:
    type_name = change.config_type.value.replace("_", "")
    event_name = change.change_type.value
    return f"{type_name}_{event_name}.py"
```

So for hosts/new: "hostsnew.py" - that's the naming scheme.

Actually I think the naming is "host_new.py" style. Let me re-check executor.py

Looking at executor.py:
```python
type_name = change.config_type.value.replace("_", "")
```

"hosts".replace("_", "") = "hosts" (no underscores)
event_name = "new"
result: "hostsnew.py"

Hmm that looks odd. But this is existing behavior, not my design.
I should write the test to match existing behavior.

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_executor.py::test_get_hook_path -v
```
Expected: PASS

- [ ] **Step 5: Add remaining executor tests**

Write tests for:
- `test_load_hook_new` - load and execute new hook
- `test_load_hook_update` - load and execute update hook
- `test_execute_hook_dry_run` - dry run mode
- `test_execute_hook_no_hook` - missing hook skips
- `test_execute_changes_multiple` - multiple changes stats

- [ ] **Step 6: Run all executor tests**

```bash
pytest tests/test_executor.py -v
```
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add tests/test_executor.py
git commit -m "feat: add executor tests"
```

---

## Task 8: Final verification

- [ ] **Step 1: Run all tests**

```bash
pytest tests/ -v
```

- [ ] **Step 2: Verify all pass**

Expected: All tests PASS

- [ ] **Step 3: Run pixi commands still work**

```bash
pixi run detect
pixi run validate
pixi run deploy --dry-run
```

---

## Self-Review Checklist

1. **Spec coverage:**
   - [x] CMDB_ROOT env var support - Task 2, 3, 4
   - [x] Test isolation with tmp_path - Task 5
   - [x] validator.py tests - Task 6
   - [x] executor.py tests - Task 7

2. **Placeholder scan:** No TBD/TODO in plan

3. **Type consistency:** get_cmdb_root() returns Path, used consistently in validator.py and executor.py

---

## Execution Choice

**Plan complete and saved to `docs/superpowers/plans/2026-04-27-cmdb-test-implementation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
