"""
Services 新增 hook 示例
"""

def run(context):
    """
    context 包含:
        - name: 文件名
        - service_name: 服务名
        - version: 版本
        - hosts: 部署目标列表
        - new: 完整的新配置
    """
    service_name = context.get("service_name")
    version = context.get("version")
    hosts = context.get("hosts", [])

    print(f"[service_add] 新增服务: {service_name}")
    print(f"              版本: {version}")
    print(f"              部署目标: {', '.join(hosts)}")

    # TODO: 填充实际的部署逻辑
    # 例如: 触发 CI/CD、调用部署脚本等

    return True
