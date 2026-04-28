# CMDB 业务校验规则设计

## 目标

为 pycmdb 添加业务校验规则，在 JSON Schema 校验的基础上，对配置进行业务逻辑校验。

## 范围

### 纳入规则

| 配置类型 | 规则 | 错误信息示例 |
|---------|------|-------------|
| hosts | 文件名（无后缀）== hostname 字段 | "文件名 web-02 与 hostname web-01 不匹配" |
| host_groups | 文件名（无后缀）== name 字段 | "文件名 web-servers 与 name web-pool 不匹配" |
| services | 文件名（无后缀）== name 字段 | "文件名 api-gateway 与 name api-gateway-match 不匹配" |

### 暂不纳入

- services version 语义化版本格式校验（后续迭代）

## 设计

### 实现方式

在 `validator.py` 中新增 `validate_business_rules()` 函数：

```python
def validate_business_rules(config_type: ConfigType, name: str, data: dict) -> list[str]:
    """
    业务规则校验
    返回错误列表，空列表表示校验通过
    """
    errors = []

    if config_type == ConfigType.HOSTS:
        hostname = data.get("hostname", "")
        if hostname and name != hostname:
            errors.append(f"文件名 {name} 与 hostname {hostname} 不匹配")

    elif config_type == ConfigType.HOST_GROUPS:
        group_name = data.get("name", "")
        if group_name and name != group_name:
            errors.append(f"文件名 {name} 与 name {group_name} 不匹配")

    elif config_type == ConfigType.SERVICES:
        svc_name = data.get("name", "")
        if svc_name and name != svc_name:
            errors.append(f"文件名 {name} 与 name {svc_name} 不匹配")

    return errors
```

### 集成

在 `validate_change()` 中调用：

```python
def validate_change(change: Change) -> tuple[bool, list[str]]:
    ...
    # 业务规则校验
    business_errors = validate_business_rules(change.config_type, change.name, new_data)
    errors.extend(business_errors)
    ...
```

### 错误信息格式

`"文件名 {文件名} 与 {字段名} {字段值} 不匹配"`

## 验收标准

1. 文件名与配置字段不匹配时，错误信息清晰指出问题
2. 校验通过时返回空错误列表
3. 每个配置类型的校验规则有对应测试
