"""Tests for scripts/executor.py"""
import pytest

from scripts.executor import (
    get_hook_path,
    get_hook_name,
    load_hook,
    execute_hook,
    execute_changes,
    build_context,
)
from scripts.detector import Change, ChangeType, ConfigType


def test_get_hook_path(cmdb_root, monkeypatch):
    """Given a Change, returns correct hook path."""
    monkeypatch.setenv("CMDB_ROOT", str(cmdb_root))

    change = Change(
        config_type=ConfigType.HOSTS,
        change_type=ChangeType.NEW,
        name="web-01",
    )

    path = get_hook_path(change)
    assert path == cmdb_root / "hooks" / "hosts_new.py"


def test_get_hook_path_host_groups(cmdb_root, monkeypatch):
    """host_groups change returns correct hook path."""
    monkeypatch.setenv("CMDB_ROOT", str(cmdb_root))

    change = Change(
        config_type=ConfigType.HOST_GROUPS,
        change_type=ChangeType.UPDATE,
        name="web-servers",
    )

    path = get_hook_path(change)
    # host_groups -> hostgroups (underscore removed), then _update
    assert path == cmdb_root / "hooks" / "hostgroups_update.py"


def test_get_hook_name():
    """get_hook_name returns correct hook filename."""
    change = Change(
        config_type=ConfigType.HOSTS,
        change_type=ChangeType.NEW,
        name="web-01",
    )

    name = get_hook_name(change)
    assert name == "hosts_new.py"


def test_load_hook_new(cmdb_root, monkeypatch):
    """Load and execute a new hook."""
    monkeypatch.setenv("CMDB_ROOT", str(cmdb_root))

    # Create a new hook file
    hook_file = cmdb_root / "hooks" / "hosts_new.py"
    hook_file.write_text('''
def run(context):
    print(f"Created {context['name']}")
    return True
''')

    change = Change(
        config_type=ConfigType.HOSTS,
        change_type=ChangeType.NEW,
        name="web-01",
    )

    hook_module = load_hook(change)
    assert hook_module is not None
    assert hasattr(hook_module, "run")


def test_load_hook_update(cmdb_root, monkeypatch):
    """Load and execute an update hook."""
    monkeypatch.setenv("CMDB_ROOT", str(cmdb_root))

    # Create an update hook file
    hook_file = cmdb_root / "hooks" / "hosts_update.py"
    hook_file.write_text('''
def run(context):
    print(f"Updated {context['name']}")
    return True
''')

    change = Change(
        config_type=ConfigType.HOSTS,
        change_type=ChangeType.UPDATE,
        name="web-01",
    )

    hook_module = load_hook(change)
    assert hook_module is not None
    assert hasattr(hook_module, "run")


def test_execute_hook_dry_run(cmdb_root, monkeypatch, capsys):
    """dry_run mode doesn't execute hook."""
    monkeypatch.setenv("CMDB_ROOT", str(cmdb_root))

    # Create a hook file
    hook_file = cmdb_root / "hooks" / "hosts_new.py"
    hook_file.write_text('''
def run(context):
    raise Exception("This should not be called")
''')

    change = Change(
        config_type=ConfigType.HOSTS,
        change_type=ChangeType.NEW,
        name="web-01",
    )

    result = execute_hook(change, None, {"hostname": "web-01"}, dry_run=True)

    assert result is True
    captured = capsys.readouterr()
    assert "[DRYRUN]" in captured.out


def test_execute_hook_no_hook(cmdb_root, monkeypatch, capsys):
    """Missing hook file returns True (skip)."""
    monkeypatch.setenv("CMDB_ROOT", str(cmdb_root))

    change = Change(
        config_type=ConfigType.HOSTS,
        change_type=ChangeType.NEW,
        name="web-01",
    )

    result = execute_hook(change, None, {"hostname": "web-01"}, dry_run=False)

    assert result is True
    captured = capsys.readouterr()
    assert "[SKIP]" in captured.out


def test_execute_hook_success(cmdb_root, monkeypatch, capsys):
    """Execute hook successfully returns True."""
    monkeypatch.setenv("CMDB_ROOT", str(cmdb_root))

    # Create a hook file that succeeds
    hook_file = cmdb_root / "hooks" / "hosts_new.py"
    hook_file.write_text('''
def run(context):
    print(f"Created {context['name']}")
    return True
''')

    change = Change(
        config_type=ConfigType.HOSTS,
        change_type=ChangeType.NEW,
        name="web-01",
    )

    result = execute_hook(change, None, {"hostname": "web-01"}, dry_run=False)

    assert result is True
    captured = capsys.readouterr()
    assert "Created web-01" in captured.out


def test_execute_changes_multiple(cmdb_root, monkeypatch):
    """execute_changes returns correct stats."""
    monkeypatch.setenv("CMDB_ROOT", str(cmdb_root))

    # Create hook files for new and update
    hook_file_new = cmdb_root / "hooks" / "hosts_new.py"
    hook_file_new.write_text('''
def run(context):
    return True
''')

    hook_file_update = cmdb_root / "hooks" / "hosts_update.py"
    hook_file_update.write_text('''
def run(context):
    return True
''')

    # Create config files
    host_new = cmdb_root / "hosts" / "config" / "web-02.yaml"
    host_new.write_text("hostname: web-02\nip: 10.0.0.2\n")

    host_existing = cmdb_root / "hosts" / "config" / "web-01.yaml"
    host_existing.write_text("hostname: web-01\nip: 10.0.0.1\n")

    changes = [
        Change(
            config_type=ConfigType.HOSTS,
            change_type=ChangeType.NEW,
            name="web-02",
            new_path=host_new,
        ),
        Change(
            config_type=ConfigType.HOSTS,
            change_type=ChangeType.UPDATE,
            name="web-01",
            old_path=host_existing,
            new_path=host_existing,
        ),
    ]

    results = execute_changes(changes, dry_run=False)

    assert results["total"] == 2
    assert results["success"] == 2
    assert results["failed"] == 0
    assert results["skipped"] == 0
    assert len(results["details"]) == 2


def test_build_context():
    """build_context creates correct context dict."""
    change = Change(
        config_type=ConfigType.HOSTS,
        change_type=ChangeType.NEW,
        name="web-01",
    )

    context = build_context(change, None, {"hostname": "web-01", "ip": "10.0.0.1"})

    assert context["change_type"] == "new"
    assert context["config_type"] == "hosts"
    assert context["name"] == "web-01"
    assert context["hostname"] == "web-01"
    assert "new" in context
