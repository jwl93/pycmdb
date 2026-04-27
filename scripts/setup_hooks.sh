#!/bin/bash
# 安装 pre-commit hook 到 .git/hooks/

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK_SOURCE="$PROJECT_ROOT/hooks/pre-commit"
HOOK_TARGET="$PROJECT_ROOT/.git/hooks/pre-commit"

if [ ! -f "$HOOK_SOURCE" ]; then
    echo "[CMDB] pre-commit hook 源文件不存在，跳过安装"
    exit 0
fi

# 确保 .git/hooks 目录存在
mkdir -p "$PROJECT_ROOT/.git/hooks"

# 复制 hook 文件，在 shebang 后插入项目路径
{
    head -n 1 "$HOOK_SOURCE"
    echo "import sys; sys.path.insert(0, '$PROJECT_ROOT')"
    tail -n +2 "$HOOK_SOURCE"
} > "$HOOK_TARGET"

# 设置执行权限
chmod +x "$HOOK_TARGET"

echo "[CMDB] pre-commit hook 已安装: $HOOK_TARGET"
