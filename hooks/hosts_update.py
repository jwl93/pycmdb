"""
Hosts 更新 hook 示例
"""

def run(context):
    """
    context 包含:
        - name: 文件名
        - hostname: 主机名
        - old: 旧配置
        - new: 新配置
    """
    hostname = context.get("hostname")
    old = context.get("old", {})
    new = context.get("new", {})

    # 对比变更的字段
    changed_fields = []
    for key in set(old.keys()) | set(new.keys()):
        if old.get(key) != new.get(key):
            changed_fields.append(key)

    print(f"[host_update] 更新主机: {hostname}")
    print(f"             变更字段: {', '.join(changed_fields)}")

    # TODO: 填充实际的更新逻辑

    return True
