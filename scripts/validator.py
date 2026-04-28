"""
关联校验模块 - 检查 host_group 引用、hosts 引用等
"""
import jsonschema
import yaml
from pathlib import Path
from typing import Optional

from scripts.detector import Change, ChangeType, ConfigType
from scripts import get_cmdb_root


class ValidationError(Exception):
    pass


def get_schema(config_type: ConfigType) -> dict:
    """加载指定类型的 JSON Schema"""
    schema_path = get_cmdb_root() / config_type.value / "_schema.json"
    if not schema_path.exists():
        return {}
    with open(schema_path) as f:
        return yaml.safe_load(f)


def get_defaults(config_type: ConfigType) -> dict:
    """加载指定类型的默认值"""
    defaults_path = get_cmdb_root() / config_type.value / "_defaults.yaml"
    if not defaults_path.exists():
        return {}
    with open(defaults_path) as f:
        return yaml.safe_load(f) or {}


def validate_config(config_type: ConfigType, name: str, data: dict) -> dict:
    """
    校验配置并应用默认值
    返回合并默认值后的完整配置
    """
    schema = get_schema(config_type)
    if not schema:
        return data

    # 应用默认值
    defaults = get_defaults(config_type)
    data = _merge_defaults(data, defaults)

    # JSON Schema 校验
    jsonschema.validate(data, schema)

    return data


def _merge_defaults(data: dict, defaults: dict) -> dict:
    """递归合并默认值"""
    result = defaults.copy()
    for key, value in data.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_defaults(value, result[key])
        else:
            result[key] = value
    return result


def validate_references(change: Change, data: Optional[dict]) -> list[str]:
    """
    校验配置中的引用是否存在
    返回错误列表，空列表表示校验通过
    """
    errors = []

    if not data:
        return errors

    if change.config_type == ConfigType.SERVICES:
        # 检查 hosts 和 host_groups 引用
        hosts_refs = data.get("hosts", [])
        for ref in hosts_refs:
            if _resolve_ref(ref) is None:
                errors.append(f"引用的 host/host_group 不存在: {ref}")

    elif change.config_type == ConfigType.HOST_GROUPS:
        # 检查 host_group 成员是否都存在
        members = data.get("members", [])
        for member in members:
            host_path = get_cmdb_root() / "hosts" / "config" / member
            group_path = get_cmdb_root() / "host_groups" / "config" / member
            if not host_path.exists() and not group_path.exists():
                errors.append(f"分组成员不存在: {member}")

    return errors


def _resolve_ref(ref: str) -> Optional[Path]:
    """解析引用，返回配置路径（如果存在）"""
    root = get_cmdb_root()
    # 先当作 host 查找
    host_path = root / "hosts" / "config" / ref
    if host_path.exists():
        return host_path

    # 再当作 host_group 查找
    group_path = root / "host_groups" / "config" / ref
    if group_path.exists():
        return group_path

    return None


def validate_change(change: Change) -> tuple[bool, list[str]]:
    """
    对单个变更进行全面校验
    返回 (是否通过, 错误列表)
    """
    errors = []

    # 获取配置内容
    from scripts.detector import get_config_content
    old_data, new_data = get_config_content(change)

    # 根据变更类型校验
    if change.change_type == ChangeType.DELETE:
        # 删除操作只需校验引用的引用
        pass  # 可扩展

    elif change.change_type == ChangeType.NEW:
        try:
            validate_config(change.config_type, change.name, new_data)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema 校验失败: {e.message}")
        refs_errors = validate_references(change, new_data)
        errors.extend(refs_errors)

    elif change.change_type == ChangeType.UPDATE:
        try:
            validate_config(change.config_type, change.name, new_data)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema 校验失败: {e.message}")
        refs_errors = validate_references(change, new_data)
        errors.extend(refs_errors)

    return len(errors) == 0, errors
