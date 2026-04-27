#!/bin/bash
# 安装 pre-commit hook 到 .git/hooks/

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK_SOURCE="$PROJECT_ROOT/hooks/pre-commit"
HOOK_TARGET="$PROJECT_ROOT/.git/hooks/pre-commit"

if [ ! -f "$HOOK_SOURCE" ]; then
    echo "[CMDB] pre-commit hook 源文件不存在，跳过安装"
    exit 0
fi

# 确保 .git/hooks 目录存在
mkdir -p "$PROJECT_ROOT/.git/hooks"

# 直接复制 hook 文件
cp "$HOOK_SOURCE" "$HOOK_TARGET"

# 设置执行权限
chmod +x "$HOOK_TARGET"

echo "[CMDB] pre-commit hook 已安装: $HOOK_TARGET"
