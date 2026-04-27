"""
Services 删除 hook 示例
"""

def run(context):
    """
    context 包含:
        - name: 文件名
        - service_name: 服务名
        - old: 被删除的配置
    """
    service_name = context.get("service_name")
    old = context.get("old", {})

    print(f"[service_delete] 删除服务: {service_name}")
    print(f"                 最后版本: {old.get('version', 'N/A')}")

    # TODO: 填充实际的删除逻辑

    return True
