"""
Services 更新 hook 示例
"""

def run(context):
    """
    context 包含:
        - name: 文件名
        - service_name: 服务名
        - old: 旧配置
        - new: 新配置
    """
    service_name = context.get("service_name")
    old = context.get("old", {})
    new = context.get("new", {})

    old_version = old.get("version")
    new_version = new.get("version")
    hosts_changed = old.get("hosts", []) != new.get("hosts", [])

    print(f"[service_update] 更新服务: {service_name}")
    if old_version != new_version:
        print(f"                 版本: {old_version} → {new_version}")
    if hosts_changed:
        print(f"                 部署目标变更: {old.get('hosts')} → {new.get('hosts')}")

    # TODO: 填充实际的更新逻辑

    return True
