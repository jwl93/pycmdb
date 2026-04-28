"""pytest fixtures and configuration"""
import os
import pytest
import shutil
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
    # Copy schemas
    for config_type in ["hosts", "host_groups", "services"]:
        src_schema = Path(__file__).parent.parent / config_type / "_schema.json"
        src_defaults = Path(__file__).parent.parent / config_type / "_defaults.yaml"
        dst = cmdb_root / config_type

        if src_schema.exists():
            shutil.copy(src_schema, dst / "_schema.json")
        if src_defaults.exists():
            shutil.copy(src_defaults, dst / "_defaults.yaml")

    return cmdb_root

@pytest.fixture
def sample_host(schema_dir):
    """Create sample host config web-01."""
    host_file = schema_dir / "hosts" / "config" / "web-01"
    host_file.write_text("hostname: web-01\nip: 10.0.0.1\n")
    return host_file

@pytest.fixture
def sample_host_group(schema_dir, sample_host):
    """Create sample host_group config web-servers."""
    group_file = schema_dir / "host_groups" / "config" / "web-servers"
    group_file.write_text("name: web-servers\nmembers:\n  - web-01\n")
    return group_file

@pytest.fixture
def sample_service(schema_dir, sample_host):
    """Create sample service config api-gateway."""
    svc_file = schema_dir / "services" / "config" / "api-gateway"
    svc_file.write_text("name: api-gateway\nversion: 1.0.0\nhosts:\n  - web-01\n")
    return svc_file