# Service Type Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deploy preview showing service info before execution, with generic and type-specific sections.

**Architecture:** Add `build_deploy_preview()` to executor.py to construct preview data, modify cli.py deploy command to display it before confirmation.

**Tech Stack:** Python, Click, PyYAML

---

## File Structure

```
scripts/
├── executor.py     # Add build_deploy_preview() function
└── cli.py          # Modify deploy to show preview before confirmation
```

---

## Task 1: Add build_deploy_preview() to executor.py

**Files:**
- Modify: `scripts/executor.py`

- [ ] **Step 1: Add build_deploy_preview() function**

Add this function after `build_context()`:

```python
def build_deploy_preview(change: Change) -> dict:
    """
    构建部署预览信息
    返回 {'generic': {...}, 'type_specific': {...}}
    """
    from scripts.detector import get_config_content

    _, new_data = get_config_content(change)

    generic = {
        'name': new_data.get('name'),
        'version': new_data.get('version'),
        'type': new_data.get('type'),
        'hosts': new_data.get('hosts', []),
    }

    type_specific = {}
    svc_type = new_data.get('type')

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

- [ ] **Step 2: Run basic test**

```bash
python -c "from scripts.executor import build_deploy_preview; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add scripts/executor.py
git commit -m "feat: add build_deploy_preview function"
```

---

## Task 2: Modify deploy command to show preview

**Files:**
- Modify: `scripts/cli.py`

- [ ] **Step 1: Add preview display function**

Add this function after `filter_changes()` and before `@cli.group()`:

```python
def format_deploy_preview(preview: dict) -> str:
    """格式化部署预览信息"""
    lines = []
    g = preview['generic']
    ts = preview['type_specific']

    lines.append("  服务: " + g['name'])
    lines.append("  类型: " + (g['type'] or 'N/A'))
    lines.append("  目标主机: " + ', '.join(g['hosts']) if g['hosts'] else "  目标主机: 无")

    if ts:
        lines.append("  配置:")
        for key, value in ts.items():
            if value is not None:
                # 格式化键名: sync_interval -> sync interval
                display_key = key.replace('_', ' ')
                lines.append(f"    {display_key}: {value}")

    return '\n'.join(lines)
```

- [ ] **Step 2: Modify deploy command to show preview**

In the `deploy()` function, after validation passes and before confirmation prompt:

Replace:
```python
    click.echo(click.style("校验通过！", fg="green"))

    # 确认执行
    if not preview:
        if not click.confirm("\n确认执行部署?"):
            click.echo("已取消部署")
            return
```

With:
```python
    click.echo(click.style("校验通过！", fg="green"))

    # 构建并显示部署预览
    preview_data = build_deploy_preview(changes[0])  # 目前只支持单服务预览
    click.echo("\n部署预览:")
    click.echo("-" * 40)
    click.echo(format_deploy_preview(preview_data))
    click.echo("-" * 40)

    # 确认执行
    if not preview:
        if not click.confirm("\n确认执行部署?"):
            click.echo("已取消部署")
            return
```

- [ ] **Step 3: Add import for build_deploy_preview**

Add to imports at top of file:
```python
from scripts.executor import execute_changes, get_hook_path, build_deploy_preview
```

- [ ] **Step 4: Test preview display**

```bash
pixi run deploy --type services --targets syncer --preview
```

Expected output should show the preview section.

- [ ] **Step 5: Commit**

```bash
git add scripts/cli.py
git commit -m "feat: add deploy preview before confirmation"
```

---

## Self-Review Checklist

1. **Spec coverage:**
   - [x] build_deploy_preview() function - Task 1
   - [x] Preview display in deploy - Task 2
   - [x] Generic info (name, version, type, hosts) - Task 1, 2
   - [x] Type-specific info (syncer fields) - Task 1, 2

2. **Placeholder scan:** No TBD/TODO in plan

3. **Type consistency:** build_deploy_preview returns dict with 'generic' and 'type_specific' keys, format_deploy_preview accesses these correctly

---

## Execution Choice

**Plan complete and saved to `docs/superpowers/plans/2026-04-27-service-type-preview-implementation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
