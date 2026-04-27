"""
HostGroups 新增 hook 示例
"""

def run(context):
    """
    context 包含:
        - name: 文件名
        - group_name: 分组名
        - members: 成员列表
        - new: 完整的新配置
    """
    group_name = context.get("group_name")
    members = context.get("members", [])

    print(f"[group_add] 新增分组: {group_name}")
    print(f"            成员: {', '.join(members)}")

    return True
