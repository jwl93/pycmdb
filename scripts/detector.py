"""
变更检测模块 - 分析 git diff，识别 NEW/DELETE/UPDATE 事件
"""
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class ChangeType(str, Enum):
    NEW = "new"
    UPDATE = "update"
    DELETE = "delete"


class ConfigType(str, Enum):
    HOSTS = "hosts"
    HOST_GROUPS = "host_groups"
    SERVICES = "services"


@dataclass
class Change:
    config_type: ConfigType
    change_type: ChangeType
    name: str  # 文件名（无后缀）
    old_path: Optional[Path] = None
    new_path: Optional[Path] = None
    diff: Optional[str] = None


def detect_changes(base_commit: Optional[str] = None) -> list[Change]:
    """
    检测 git 变更，返回 Change 列表
    """
    cmd = ["git", "diff", "--name-status"]
    if base_commit:
        cmd.append(base_commit)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []

    changes = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        status, *paths = line.split("\t")
        path = paths[0] if paths else ""

        change = _parse_change(status, path)
        if change:
            changes.append(change)

    return changes


def _parse_change(status: str, path: str) -> Optional[Change]:
    """
    解析 git diff --name-status 的单行输出
    """
    # path 格式: hosts/config/web-01
    parts = path.split("/")
    if len(parts) < 2 or parts[0] not in ("hosts", "host_groups", "services"):
        return None

    config_type = ConfigType(parts[0])
    name = parts[-1]  # 文件名（无后缀）

    if status == "D":
        change_type = ChangeType.DELETE
        old_path = Path(path)
        new_path = None
    elif status == "A":
        change_type = ChangeType.NEW
        old_path = None
        new_path = Path(path)
    else:  # M, R 等
        change_type = ChangeType.UPDATE
        old_path = Path(path)
        new_path = Path(path)

    return Change(
        config_type=config_type,
        change_type=change_type,
        name=name,
        old_path=old_path,
        new_path=new_path,
    )


def get_config_content(change: Change) -> tuple[Optional[dict], Optional[dict]]:
    """
    获取变更前后的配置内容
    """
    import yaml

    old_content = None
    new_content = None

    if change.old_path:
        try:
            with open(change.old_path) as f:
                old_content = yaml.safe_load(f)
        except FileNotFoundError:
            pass

    if change.new_path:
        try:
            with open(change.new_path) as f:
                new_content = yaml.safe_load(f)
        except FileNotFoundError:
            pass

    return old_content, new_content
