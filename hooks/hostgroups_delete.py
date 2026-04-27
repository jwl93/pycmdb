"""
HostGroups 删除 hook 示例
"""

def run(context):
    """
    context 包含:
        - name: 文件名
        - group_name: 分组名
        - old: 被删除的配置
    """
    group_name = context.get("group_name")
    old = context.get("old", {})
    members = old.get("members", [])

    print(f"[group_delete] 删除分组: {group_name}")
    print(f"               原成员: {', '.join(members)}")

    return True
