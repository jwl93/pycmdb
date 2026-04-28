"""Tests for scripts/validator.py"""
import pytest
from jsonschema import ValidationError

from scripts.validator import validate_config, validate_references
from scripts.detector import ConfigType, Change, ChangeType


def test_validate_config_valid(schema_dir, monkeypatch):
    """Valid host config should pass validation."""
    monkeypatch.setenv("CMDB_ROOT", str(schema_dir))

    data = {"hostname": "web-01", "ip": "10.0.0.1"}
    result = validate_config(ConfigType.HOSTS, "web-01", data)

    assert result["hostname"] == "web-01"
    assert result["ip"] == "10.0.0.1"


def test_validate_config_invalid(schema_dir, monkeypatch):
    """Invalid config (wrong ip format) should fail schema validation."""
    monkeypatch.setenv("CMDB_ROOT", str(schema_dir))

    data = {"hostname": "web-01", "ip": "not-an-ip"}

    with pytest.raises(ValidationError) as exc_info:
        validate_config(ConfigType.HOSTS, "web-01", data)

    assert "ipv4" in str(exc_info.value)


def test_merge_defaults(schema_dir, monkeypatch):
    """Default values should be merged into config."""
    monkeypatch.setenv("CMDB_ROOT", str(schema_dir))

    # Only provide hostname and ip, defaults should be merged
    data = {"hostname": "web-01", "ip": "10.0.0.1"}
    result = validate_config(ConfigType.HOSTS, "web-01", data)

    # Check that defaults are merged
    assert result["host_group"] == ["untagged"]
    assert result["ssh"]["port"] == 22
    assert result["ssh"]["user"] == "root"
    assert result["labels"] == {}
    assert result["vars"] == {}


def test_validate_references_valid(schema_dir, monkeypatch, sample_host):
    """Referenced host exists, should pass."""
    monkeypatch.setenv("CMDB_ROOT", str(schema_dir))

    change = Change(
        config_type=ConfigType.HOST_GROUPS,
        change_type=ChangeType.UPDATE,
        name="test-group"
    )
    data = {"name": "test-group", "members": ["web-01"]}

    errors = validate_references(change, data)

    assert errors == []


def test_validate_references_invalid(schema_dir, monkeypatch):
    """Referenced host/host_group missing, should return error."""
    monkeypatch.setenv("CMDB_ROOT", str(schema_dir))

    change = Change(
        config_type=ConfigType.SERVICES,
        change_type=ChangeType.NEW,
        name="test-service"
    )
    data = {"name": "test-service", "version": "1.0.0", "hosts": ["nonexistent-host"]}

    errors = validate_references(change, data)

    assert len(errors) == 1
    assert "nonexistent-host" in errors[0]


def test_validate_host_group_members_valid(schema_dir, monkeypatch, sample_host):
    """All host_group members exist, should pass."""
    monkeypatch.setenv("CMDB_ROOT", str(schema_dir))

    change = Change(
        config_type=ConfigType.HOST_GROUPS,
        change_type=ChangeType.NEW,
        name="web-servers"
    )
    data = {"name": "web-servers", "members": ["web-01"]}

    errors = validate_references(change, data)

    assert errors == []


def test_validate_host_group_members_missing(schema_dir, monkeypatch):
    """host_group member missing, should return error."""
    monkeypatch.setenv("CMDB_ROOT", str(schema_dir))

    change = Change(
        config_type=ConfigType.HOST_GROUPS,
        change_type=ChangeType.NEW,
        name="web-servers"
    )
    data = {"name": "web-servers", "members": ["nonexistent-host"]}

    errors = validate_references(change, data)

    assert len(errors) == 1
    assert "nonexistent-host" in errors[0]


def test_validate_services_references_valid(schema_dir, monkeypatch, sample_host, sample_host_group):
    """Service references existing hosts/groups, should pass."""
    monkeypatch.setenv("CMDB_ROOT", str(schema_dir))

    change = Change(
        config_type=ConfigType.SERVICES,
        change_type=ChangeType.NEW,
        name="api-gateway"
    )
    data = {
        "name": "api-gateway",
        "version": "1.0.0",
        "hosts": ["web-01", "web-servers"]
    }

    errors = validate_references(change, data)

    assert errors == []


def test_validate_change_new(cmdb_root, monkeypatch, schema_dir, sample_host):
    """Test validate_change for NEW config type."""
    import os
    monkeypatch.setenv("CMDB_ROOT", str(cmdb_root))

    from scripts.validator import validate_change
    from scripts.detector import ConfigType, Change, ChangeType, get_config_content

    # Create a change object for a new host
    change = Change(
        config_type=ConfigType.HOSTS,
        change_type=ChangeType.NEW,
        name="web-02",
        new_path=cmdb_root / "hosts" / "config" / "web-02.yaml"
    )

    # Write the config file
    (cmdb_root / "hosts" / "config" / "web-02.yaml").write_text(
        "hostname: web-02\nip: 10.0.0.2\n"
    )

    valid, errors = validate_change(change)
    assert valid is True
    assert len(errors) == 0