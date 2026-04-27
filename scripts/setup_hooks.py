"""
安装 pre-commit hook 到 .git/hooks/
"""
import os
import stat
import sys
from pathlib import Path


def install_hook():
    # 项目根目录
    project_root = Path(__file__).parent.parent
    hook_source = project_root / "hooks" / "pre-commit"
    hook_target = Path(".git") / "hooks" / "pre-commit"

    if not hook_source.exists():
        print("[CMDB] pre-commit hook 源文件不存在，跳过安装")
        return

    # 确保 .git/hooks 目录存在
    hook_target.parent.mkdir(parents=True, exist_ok=True)

    # 复制 hook 文件，内容追加项目路径
    with open(hook_source, "r") as src:
        content = src.read()

    # 在 shebang 后插入 path setup
    hook_content = f"""#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, '{project_root.absolute()}')

"""

    # 找到原文件中的 if __name__ == "__main__" 部分，只取 main 部分
    main_start = content.find("def main():")
    if main_start != -1:
        main_content = content[main_start:]
        hook_content += main_content
    else:
        hook_content += content

    with open(hook_target, "w") as dst:
        dst.write(hook_content)

    # 设置执行权限
    os.chmod(hook_target, os.stat(hook_target).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"[CMDB] pre-commit hook 已安装: {hook_target}")


if __name__ == "__main__":
    # 只在 git 仓库中运行
    if Path(".git").exists():
        install_hook()
