# pycmdb

Git-based CMDB - 使用 Git 作为配置管理数据库，通过文件变更检测实现配置变更追踪和发布。

## 快速开始

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
publish/
├── hosts/           # 主机配置
│   ├── config/     # 主机配置文件
│   ├── _schema.json
│   └── _defaults.yaml
├── host_groups/    # 主机组配置
│   ├── config/
│   ├── _schema.json
│   └── _defaults.yaml
└── services/       # 服务配置
    ├── config/
    ├── _schema.json
    └── _defaults.yaml
```

## 配置类型

### hosts - 主机配置

在 `publish/hosts/config/` 下创建文件，文件名即主机名：

```yaml
# publish/hosts/config/web-01
hostname: web-01
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

在 `publish/host_groups/config/` 下创建文件：

```yaml
# publish/host_groups/config/web-servers
name: web-servers
description: Web 服务器组
```

**注意:** 主机组成员是动态计算的，不需要 `members` 字段。系统会遍历所有 hosts 配置，根据 `host_group` 字段自动计算每个组包含哪些主机。

### services - 服务配置

在 `publish/services/config/` 下创建文件：

```yaml
# publish/services/config/api-gateway
name: api-gateway
version: 1.0.0
hosts:
  - web-01
  - web-02
deployment:
  start_time: "02:00"
  end_time: "06:00"
vars:
  port: 8080
  workers: 4
```

## CLI 命令

```bash
# 检测所有变更
pixi run detect

# 按类型过滤 (hosts/host_groups/services)
pixi run detect --type hosts

# 指定目标文件
pixi run detect --targets web-01,web-02

# 校验变更
pixi run validate

# 部署变更
pixi run deploy

# 按类型部署
pixi run deploy --type services

# 预览模式（不执行）
pixi run deploy --preview
```

## Hooks

变更执行时会调用对应的 hook 脚本。Hook 文件位于 `hooks/` 目录：

| Hook 文件 | 触发时机 |
|----------|---------|
| `hosts_new.py` | 新增主机 |
| `hosts_update.py` | 更新主机 |
| `hosts_delete.py` | 删除主机 |
| `hostgroups_new.py` | 新增主机组 |
| `hostgroups_update.py` | 更新主机组 |
| `hostgroups_delete.py` | 删除主机组 |
| `services_new.py` | 新增服务 |
| `services_update.py` | 更新服务 |
| `services_delete.py` | 删除服务 |

### Hook 示例

```python
# hooks/hosts_new.py
def run(context):
    """
    context 包含:
        - name: 文件名
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
```

### Hook 上下文变量

**hosts:**
- `name` - 文件名（无后缀）
- `hostname` - 主机名
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
- `hosts` - 部署目标列表
- `new` / `old` - 完整配置

## 业务规则

配置校验除了 JSON Schema 验证外，还有业务规则校验：

| 配置类型 | 规则 |
|---------|------|
| hosts | 文件名必须与 `hostname` 字段一致 |
| host_groups | 文件名必须与 `name` 字段一致 |
| services | 文件名必须与 `name` 字段一致 |

## 自动提交

`pixi run deploy` 执行成功后，会自动将变更 `git add` 并 `commit`，然后 `push` 到远程仓库。

commit 信息格式：`{新增|更新|删除} {类型}: {文件名}`

## 命名规范

- **hostname/name**: 小写字母开头，只含 `a-z0-9-`
- **version**: 语义化版本 `x.y.z`
