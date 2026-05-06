# Service Type 预检查设计

## 目标

在 deploy 执行前显示详细的部署预览信息，分通用部分和 service-type 特定部分。

## 设计

### 预检查信息分层

**通用部分 (所有服务):**
- 服务名 (name)
- 版本 (version)
- 服务类型 (type)
- 部署目标 (hosts)

**Service-type 特定部分:**
- 根据 `type` 字段动态提取相关配置字段
- 使用 `deployment` 和 `vars` 中的字段，按 type 定义展示

### 实现方式

在 `scripts/executor.py` 中新增 `build_deploy_preview()` 函数：

```python
def build_deploy_preview(change: Change) -> dict:
    """
    构建部署预览信息
    返回 {'generic': {...}, 'type_specific': {...}}
    """
    _, new_data = get_config_content(change)

    generic = {
        'name': new_data.get('name'),
        'version': new_data.get('version'),
        'type': new_data.get('type'),
        'hosts': new_data.get('hosts', []),
    }

    type_specific = {}
    svc_type = new_data.get('type')

    # 根据 type 提取特定字段
    if svc_type == 'syncer':
        deployment = new_data.get('deployment', {})
        vars_data = new_data.get('vars', {})
        type_specific = {
            'src_host': deployment.get('src_host'),
            'src_path': deployment.get('src_path'),
            'dst_path': deployment.get('dst_path'),
            'sync_interval': vars_data.get('sync_interval'),
        }

    return {'generic': generic, 'type_specific': type_specific}
```

### 预检查输出格式

```
检测到以下变更:
------------------------------------------------------------
  services     new     syncer
------------------------------------------------------------
共 1 项变更

校验变更项...
[OK] services/syncer
校验通过！

部署预览:
  服务: syncer
  类型: syncer
  目标主机: web-01, web-02
  同步配置:
    源: db-master:/data/backup
    目标: /data/synced
    间隔: 300s

确认执行部署? [y/n]
```

## 验收标准

1. deploy 前显示部署预览信息
2. 通用部分显示 name, version, type, hosts
3. type 特定部分根据 type 字段动态显示
4. 确认提示在预览信息之后
