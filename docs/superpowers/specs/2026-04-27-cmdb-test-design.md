# CMDB 测试设计

## 目标

为 pycmdb 项目添加基础测试，覆盖配置校验和 hook 执行逻辑，作为项目的基线测试。

## 范围

### 纳入测试

- `scripts/validator.py` - schema 校验、引用校验
- `scripts/executor.py` - hook 加载和执行

### 暂不纳入

- `scripts/detector.py` - 变更检测（后续单独处理）
- Git 相关集成测试

## 设计

### 1. 项目根目录配置

**实现方式：** 环境变量 `CMDB_ROOT`，默认当前目录 `.`

```python
import os

def get_cmdb_root() -> Path:
    return Path(os.environ.get("CMDB_ROOT", "."))
```

**测试时：** 使用 `monkeypatch.setenv("CMDB_ROOT", str(tmp_path))` 切换到临时目录

### 2. 测试文件组织

```
tests/
├── __init__.py
├── conftest.py          # fixtures、mock 设置
├── test_validator.py    # validator 模块测试
└── test_executor.py      # executor 模块测试
```

### 3. 测试隔离策略

- 使用 pytest 的 `tmp_path` fixture 创建临时目录
- 每个测试独立的目录结构（hosts/config、host_groups/config、services/config）
- hook 测试用临时 hook 文件，测试完自动清理
- 不触及真实 git 仓库

### 4. detector.py 改动

**目标：** 使用 GitPython 库替代 `subprocess.run(["git", ...])`

**改动位置：** `scripts/detector.py` 的 `detect_changes` 函数

**当前逻辑：**
```python
result = subprocess.run(cmd, capture_output=True, text=True)
```

**新逻辑：**
```python
from git import Repo
repo = Repo(".")
# 使用 GitPython API 获取变更
```

**注意：** 保持原有接口不变，返回 `list[Change]`

### 5. 测试用例设计

#### test_validator.py

| 测试函数 | 描述 |
|---------|------|
| `test_validate_config_valid` | 给定合法配置，校验通过 |
| `test_validate_config_invalid` | 给定非法配置，校验失败并返回错误信息 |
| `test_merge_defaults` | 默认值正确合并到配置 |
| `test_validate_references_valid` | 引用存在的 host/host_group，通过 |
| `test_validate_references_invalid` | 引用不存在的 host/host_group，返回错误 |
| `test_validate_host_group_members` | host_group 成员都存在，通过 |
| `test_validate_host_group_members_missing` | host_group 成员有不存在，报错 |
| `test_validate_services_references` | service 引用的 hosts/groups 都存在，通过 |

#### test_executor.py

| 测试函数 | 描述 |
|---------|------|
| `test_get_hook_path` | 给定 change，返回正确的 hook 路径 |
| `test_load_hook_new` | 加载新增 hook，执行 run 函数 |
| `test_load_hook_update` | 加载更新 hook，执行 run 函数 |
| `test_load_hook_delete` | 加载删除 hook，执行 run 函数 |
| `test_execute_hook_dry_run` | dry_run 模式不真正执行 |
| `test_execute_hook_no_hook` | hook 文件不存在时跳过 |
| `test_execute_changes_multiple` | 执行多个变更，返回正确统计 |

### 6. Fixture 设计 (conftest.py)

```python
import pytest
from pathlib import Path

@pytest.fixture
def cmdb_root(tmp_path):
    """创建临时 CMDB_ROOT 目录结构"""
    (tmp_path / "hosts" / "config").mkdir(parents=True)
    (tmp_path / "host_groups" / "config").mkdir(parents=True)
    (tmp_path / "services" / "config").mkdir(parents=True)
    (tmp_path / "hooks").mkdir()
    return tmp_path

@pytest.fixture
def sample_host(cmdb_root):
    """创建示例 host 配置"""
    host_file = cmdb_root / "hosts" / "config" / "web-01.yaml"
    host_file.write_text("hostname: web-01\nip: 10.0.0.1\n")
    return host_file

@pytest.fixture
def sample_host_group(cmdb_root, sample_host):
    """创建示例 host_group 配置"""
    group_file = cmdb_root / "host_groups" / "config" / "web-servers.yaml"
    group_file.write_text("name: web-servers\nmembers:\n  - web-01\n")
    return group_file
```

### 7. 测试数据

测试配置使用内联 YAML 数据，不依赖外部 fixtures 文件。

## 依赖

```toml
[dependencies]
python = ">=3.10"
pyyaml = "*"
jsonschema = "*"
jinja2 = "*"
gitpython = "*"  # 新增

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## 验收标准

1. `pytest tests/` 运行全部测试通过
2. 测试可重复运行，互不干扰
3. 测试覆盖 validator.py 和 executor.py 的核心逻辑
4. 不触及真实 git 仓库
