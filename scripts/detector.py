"""
变更检测模块 - 分析 git diff，识别 NEW/DELETE/UPDATE 事件
"""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml
from git import Repo


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

    - If base_commit provided: compares base_commit..HEAD (committed changes)
    - If no base_commit: compares working tree to index (uncommitted + recently committed)
    """
    try:
        repo = Repo(".")
    except Exception:
        return []

    changes = []

    if base_commit:
        # Compare base_commit to HEAD for committed changes
        try:
            repo.commit(base_commit)
            commit_range = f"{base_commit}..HEAD"
            diffs = repo.head.commit.diff(commit_range)
            for item in diffs:
                change = _item_to_change(item)
                if change:
                    changes.append(change)
        except Exception:
            pass
    else:
        # No base_commit: detect working tree changes
        # Compare working tree to index (unstaged changes)
        try:
            diffs = repo.index.diff(None)  # None = compare working tree to index
            for item in diffs:
                change = _item_to_change(item)
                if change:
                    changes.append(change)
        except Exception:
            pass

        # Also detect staged changes (in index but not in HEAD)
        try:
            diffs = repo.index.diff("HEAD")
            for item in diffs:
                change = _item_to_change(item)
                if change:
                    changes.append(change)
        except Exception:
            pass

        # Detect untracked files
        for fname in repo.untracked_files:
            change = _parse_porcelain_line(f"??\t{fname}")
            if change:
                changes.append(change)

    return changes


def _item_to_change(item) -> Optional[Change]:
    """
    Convert GitPython Diff object to Change object
    """
    # Determine status from GitPython flags
    if item.new_file:
        status = "A"
    elif item.deleted_file:
        status = "D"
    elif item.renamed_file:
        status = "R"
    else:
        status = "M"

    path = item.a_path if item.deleted_file else item.b_path

    return _parse_change(status, path)


def _parse_porcelain_line(line: str) -> Optional[Change]:
    """
    Parse a line from git status --porcelain format
    """
    parts = line.split("\t")
    if len(parts) < 2:
        return None

    status = parts[0]
    path = parts[1]

    return _parse_change(status, path)


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
    elif status == "A" or status == "??":
        # "A" = added in diff, "??" = untracked file in git status
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
