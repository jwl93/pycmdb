"""
脚本执行器 - 调用对应的 hooks 脚本
"""
import importlib.util
import sys
from pathlib import Path
from typing import Optional

from scripts.detector import Change, ChangeType, ConfigType


def get_hook_name(change: Change) -> str:
    """获取对应的 hook 文件名"""
    type_name = change.config_type.value.replace("_", "")
    event_name = change.change_type.value
    return f"{type_name}_{event_name}.py"


def get_hook_path(change: Change) -> Path:
    """获取 hook 文件路径"""
    return Path("hooks") / get_hook_name(change)


def load_hook(change: Change):
    """动态加载 hook 模块"""
    hook_path = get_hook_path(change)
    if not hook_path.exists():
        return None

    spec = importlib.util.spec_from_file_location("hook", hook_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["hook"] = module
        spec.loader.exec_module(module)
        return module

    return None


def build_context(change: Change, old_data: Optional[dict], new_data: Optional[dict]) -> dict:
    """
    构建传递给 hook 的上下文
    """
    context = {
        "change_type": change.change_type.value,
        "config_type": change.config_type.value,
        "name": change.name,
    }

    if old_data:
        context["old"] = old_data
    if new_data:
        context["new"] = new_data

    # hosts 相关上下文
    if change.config_type == ConfigType.HOSTS:
        context["hostname"] = new_data.get("hostname") if new_data else (old_data.get("hostname") if old_data else change.name)

    # services 相关上下文
    elif change.config_type == ConfigType.SERVICES:
        if new_data:
            context["service_name"] = new_data.get("name")
            context["version"] = new_data.get("version")
            context["hosts"] = new_data.get("hosts", [])

    # host_groups 相关上下文
    elif change.config_type == ConfigType.HOST_GROUPS:
        if new_data:
            context["group_name"] = new_data.get("name")
            context["members"] = new_data.get("members", [])

    return context


def execute_hook(change: Change, old_data: Optional[dict], new_data: Optional[dict], dry_run: bool = False) -> bool:
    """
    执行对应的 hook 脚本
    返回是否执行成功
    """
    hook_path = get_hook_path(change)

    if not hook_path.exists():
        print(f"[SKIP] 未找到 hook: {hook_path}")
        return True  # 没找到 hook 算成功

    context = build_context(change, old_data, new_data)

    if dry_run:
        print(f"[DRYRUN] 将执行: {hook_path}")
        print(f"         上下文: {context}")
        return True

    # 动态加载并执行
    hook_module = load_hook(change)
    if hook_module and hasattr(hook_module, "run"):
        try:
            return hook_module.run(context)
        except Exception as e:
            print(f"[ERROR] hook 执行失败: {e}")
            return False

    return False


def execute_changes(changes: list[Change], dry_run: bool = False) -> dict:
    """
    执行一组变更
    返回执行结果统计
    """
    from scripts.detector import get_config_content

    results = {
        "total": len(changes),
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "details": [],
    }

    for change in changes:
        old_data, new_data = get_config_content(change)
        success = execute_hook(change, old_data, new_data, dry_run=dry_run)

        results["details"].append({
            "name": change.name,
            "type": change.config_type.value,
            "event": change.change_type.value,
            "success": success,
        })

        if success:
            results["success"] += 1
        else:
            results["failed"] += 1

    return results
