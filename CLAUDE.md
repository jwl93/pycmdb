# pycmdb - Git-based CMDB

## 项目概述

Git-based CMDB with change detection and local deployment. 使用 Git 作为配置管理数据库，通过文件变更检测实现配置变更追踪和发布。

## 环境配置

- **包管理**: pixi
- **Python**: >=3.10
- **依赖**: pyyaml, jsonschema, jinja2

### 常用命令

```bash
# 安装依赖
pixi install

# 检测变更
pixi run detect

# 校验变更
pixi run validate

# 部署变更
pixi run deploy
```

## 目录结构

```
pycmdb/
├── hosts/           # 主机配置 (config/*.yaml)
│   ├── _schema.json # JSON Schema 验证
│   └── _defaults.yaml
├── host_groups/     # 主机组配置
│   ├── _schema.json
│   └── _defaults.yaml
├── services/        # 服务配置
│   ├── _schema.json
│   └── _defaults.yaml
├── scripts/         # CLI 核心代码
│   ├── cli.py       # CLI 入口 (detect/validate/deploy 命令)
│   ├── detector.py  # 变更检测
│   ├── executor.py # 变更执行
│   ├── validator.py # 配置校验
│   └── setup_hooks.py
├── hooks/           # Git hooks (pre-commit)
│   ├── hosts_*.py
│   ├── hostgroups_*.py
│   └── services_*.py
└── pixi.toml        # pixi 配置
```

## 配置类型

每种配置类型 (hosts/host_groups/services) 都有:
- **config/*.yaml**: 配置文件
- **_schema.json**: JSON Schema 验证规则
- **_defaults.yaml**: 默认值

### 命名规范

- **hostname/name**: 小写字母开头，只含 `a-z0-9-`
- **version**: 语义化版本 `x.y.z`

## CLI 架构

- `scripts.cli`: Click 入口，提供 detect/validate/deploy 命令
- `scripts.detector`: 检测 git 变更，返回 Change 对象列表
- `scripts.validator`: 校验配置完整性和关联关系
- `scripts.executor`: 执行变更，调用 hooks/

## hooks 机制

变更执行时会调用对应类型的 hook 脚本:
- `hooks/{type}_new.py` - 新增配置
- `hooks/{type}_update.py` - 更新配置
- `hooks/{type}_delete.py` - 删除配置

Git pre-commit hook 位于 `hooks/pre-commit`，通过 `scripts/setup_hooks.py` 安装。

## 业务校验规则

配置校验除了 JSON Schema 验证外，还有业务规则校验:

| 配置类型 | 规则 | 错误信息示例 |
|---------|------|-------------|
| hosts | 文件名（无后缀）== hostname | `文件名 web-02 与 hostname web-01 不匹配` |
| host_groups | 文件名（无后缀）== name | `文件名 db-servers 与 name web-servers 不匹配` |
| services | 文件名（无后缀）== name | `文件名 gateway 与 name api-gateway 不匹配` |

## 自动提交规则

`pixi run deploy` 执行成功后，会自动将变更文件 git add 并 commit。

commit 信息格式: `{新增|更新|删除} {hosts|host_groups|services}: {文件名}`
