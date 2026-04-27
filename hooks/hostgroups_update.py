"""
HostGroups 更新 hook 示例
"""

def run(context):
    """
    context 包含:
        - name: 文件名
        - group_name: 分组名
        - old: 旧配置
        - new: 新配置
    """
    group_name = context.get("group_name")
    old = context.get("old", {})
    new = context.get("new", {})

    old_members = set(old.get("members", []))
    new_members = set(new.get("members", []))

    added = new_members - old_members
    removed = old_members - new_members

    print(f"[group_update] 更新分组: {group_name}")
    if added:
        print(f"               新增成员: {', '.join(added)}")
    if removed:
        print(f"               移除成员: {', '.join(removed)}")

    return True
