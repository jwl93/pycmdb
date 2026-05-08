# pycmdb

Git-based CMDB - 使用 Git 作为配置管理数据库，通过文件变更检测实现配置变更追踪和发布。

## 特性

- **Git 记录变更** - 所有配置变更通过 Git 管理，可追溯、可审计、可回滚
- **变更检测** - 自动检测 git diff，识别新增/修改/删除
- **配置校验** - JSON Schema + 业务规则校验，确保配置合法
- **部署锁** - 文件锁防止并发部署冲突
- **Web 界面** - 浏览器操作，支持文件编辑、部署、查看历史
- **自动提交** - 部署成功自动 git commit/push

## 快速开始

```bash
# 安装依赖
pixi install

# Web 界面（浏览器访问 http://localhost:5000）
pixi run web

# CLI 命令
pixi run detect          # 检测变更
pixi run validate       # 校验变更
pixi run deploy         # 部署变更
```

## 目录结构

```
pycmdb/
├── publish/              # 用户可编辑的配置目录
│   ├── hosts/          # 主机配置
│   │   ├── config/     # 配置文件
│   │   ├── _schema.json
│   │   └── _defaults.yaml
│   ├── host_groups/    # 主机组配置
│   │   ├── config/
│   │   ├── _schema.json
│   │   └── _defaults.yaml
│   └── services/       # 服务配置
│       ├── config/
│       ├── _schema.json
│       └── _defaults.yaml
├── scripts/            # CLI 核心代码
├── hooks/              # Git hooks (pre-commit)
├── .logs/              # 操作日志（按日期存储）
└── pixi.toml
```

## 配置类型

### hosts - 主机配置

```yaml
# publish/hosts/config/web-01
name: web-01
ip: 10.0.1.1
host_group:
  - web
  - prod
ssh:
  port: 22
  user: deploy
labels:
  environment: production
  role: webserver
```

### host_groups - 主机组配置

```yaml
# publish/host_groups/config/web-servers
name: web-servers
description: Web 服务器组
```

**注意:** 主机组成员是动态计算的，不需要 `members` 字段。系统会遍历所有 hosts 配置，根据 `host_group` 字段自动计算每个组包含哪些主机。

### services - 服务配置

```yaml
# publish/services/config/api-gateway
name: api-gateway
version: 1.0.0
type: syncer
hosts:
  - web-01
  - web-02
  - group:web-servers   # host_group 引用会自动展开
deployment:
  src_host: 10.0.1.10
  src_path: /data/logs
  dst_path: /var/log/app
vars:
  sync_interval: 300
  workers: 4
```

## CLI 命令

```bash
# 检测变更
pixi run detect

# 按类型过滤 (hosts/host_groups/services)
pixi run detect --type hosts

# 指定目标文件
pixi run detect --targets web-01,web-02

# JSON 格式输出
pixi run detect --json

# 校验变更
pixi run validate

# 校验所有配置
pixi run validate --all

# 部署变更
pixi run deploy

# 部署全部（重新部署）
pixi run deploy --all

# 部署指定类型/目标
pixi run deploy --type services --targets api-gateway
```

## Web 界面

启动 `pixi run web` 后访问 http://localhost:5000

### 功能

- **变更管理** - 查看当前 git 变更、校验、部署
- **文件编辑** - 可视化编辑配置文件，支持新建/删除/预校验
- **变更历史** - 查看 git 提交历史，对比文件 diff
- **操作日志** - 按日期查看操作记录

### 重新部署

"重新部署"功能不依赖当前 git diff，允许选择任意配置文件执行部署。适合：
- 配置未变化但需要重新执行 hook
- 配置文件存在但不在当前变更列表中

## Hooks

变更执行时会调用对应的 hook 脚本：

| Hook 文件 | 触发时机 |
|----------|---------|
| `hostgroups_new.py` | 新增主机组 |
| `hostgroups_update.py` | 更新主机组 |
| `hostgroups_delete.py` | 删除主机组 |
| `hosts_new.py` | 新增主机 |
| `hosts_update.py` | 更新主机 |
| `hosts_delete.py` | 删除主机 |
| `services_new.py` | 新增服务 |
| `services_update.py` | 更新服务 |
| `services_delete.py` | 删除服务 |

### Hook 上下文变量

**hosts:**
- `name` - 文件名（无后缀）
- `name` - 主机名（与文件名一致）
- `ip` - IP 地址
- `host_group` - 分组列表
- `new` / `old` - 完整配置

**host_groups:**
- `name` - 文件名（无后缀）
- `group_name` - 组名
- `new` / `old` - 完整配置
- 注意: 组成员是动态从 hosts 的 `host_group` 字段计算的

**services:**
- `name` - 文件名（无后缀）
- `service_name` - 服务名
- `version` - 版本
- `hosts` - 部署目标列表（含 host_group 引用）
- `new` / `old` - 完整配置

## 业务规则

配置校验除了 JSON Schema 验证外，还有业务规则校验：

| 配置类型 | 规则 | 错误信息示例 |
|---------|------|-------------|
| hosts | 文件名（无后缀）== name | `文件名 web-02 与 name web-01 不匹配` |
| host_groups | 文件名（无后缀）== name | `文件名 db-servers 与 name web-servers 不匹配` |
| services | 文件名（无后缀）== name | `文件名 gateway 与 name api-gateway 不匹配` |

## 部署锁

deploy 命令使用文件锁防止并发执行：

- 锁文件: `.deploy.lock`
- 自动清理: 进程崩溃后锁会自动释放
- 超时: 锁超过 30 分钟自动过期

## 自动提交

`pixi run deploy` 执行成功后，会自动将变更 `git add` 并 `commit`，然后 `push` 到远程仓库。

commit 信息格式：`{新增|更新|删除} {类型}: {文件名}`

## 命名规范

- **name**: 小写字母开头，只含 `a-z0-9-`
- **version**: 语义化版本 `x.y.z`

## services.hosts 字段格式

独立 host 直接写名称，host_group 使用 `group:` 前缀：

```yaml
hosts:
  - web-01                    # 独立 host
  - web-02                    # 独立 host
  - group:web-servers         # host_group，会展开为所有成员
```
