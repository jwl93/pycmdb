"""
Hosts 删除（下线）hook 示例
"""

def run(context):
    """
    context 包含:
        - name: 文件名
        - hostname: 主机名
        - old: 被删除的配置
    """
    hostname = context.get("hostname")
    old = context.get("old", {})

    print(f"[host_delete] 下线主机: {hostname}")
    print(f"              IP: {old.get('ip', 'N/A')}")

    # TODO: 填充实际的下线逻辑
    # 例如: 关闭服务、移除监控、清理 DNS 等

    return True
