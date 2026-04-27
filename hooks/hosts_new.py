"""
Hosts 新增 hook 示例
"""

def run(context):
    """
    context 包含:
        - name: 文件名（无后缀）
        - hostname: 主机名
        - ip: IP 地址
        - host_group: 分组列表
        - new: 完整的新配置
    """
    hostname = context.get("hostname")
    ip = context.get("ip")
    groups = context.get("host_group", [])

    print(f"[host_add] 新增主机: {hostname} ({ip})")
    print(f"          分组: {', '.join(groups)}")

    # TODO: 填充实际的部署逻辑
    # 例如: 调用 Ansible、SSH 远程命令等

    return True
