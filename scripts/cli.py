"""
CLI 入口 - cmdbctl 命令行工具
"""
import click
from scripts.detector import detect_changes, get_config_content, ChangeType
from scripts.validator import validate_change
from scripts.executor import execute_changes, get_hook_path


def filter_changes(changes, config_type=None, targets=None):
    """根据 config_type 和 targets 过滤变更"""
    if config_type:
        changes = [c for c in changes if c.config_type.value == config_type]
    if targets:
        target_list = [t.strip() for t in targets.split(",")]
        changes = [c for c in changes if c.name in target_list]
    return changes


def color_change_type(change_type):
    """根据变更类型返回带颜色的字符串"""
    if change_type == ChangeType.NEW:
        return click.style(f"{change_type.value:6}", fg="green")
    elif change_type == ChangeType.DELETE:
        return click.style(f"{change_type.value:6}", fg="red")
    elif change_type == ChangeType.UPDATE:
        return click.style(f"{change_type.value:6}", fg="yellow")
    return change_type.value


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
def cli():
    """Git-based CMDB - 本地变更检测与发布工具"""
    pass


@cli.command()
@click.option("--base", default=None, help="基准 commit，默认为 HEAD")
@click.option("--type", "config_type", help="按类型过滤 (hosts/host_groups/services)")
@click.option("--targets", help="指定目标文件，逗号分隔 (如 web-01,web-02)")
def detect(base, config_type, targets):
    """检测变更项，识别 new/delete/update 事件"""
    changes = detect_changes(base)
    changes = filter_changes(changes, config_type, targets)

    if not changes:
        click.echo("未检测到变更")
        return

    click.echo("\n检测到以下变更:")
    click.echo("-" * 60)

    for c in changes:
        colored_type = color_change_type(c.change_type)
        click.echo(f"  {c.config_type.value:12} {colored_type}  {c.name}")

    click.echo("-" * 60)
    click.echo(f"共 {len(changes)} 项变更")


@cli.command()
@click.option("--type", "config_type", help="按类型过滤 (hosts/host_groups/services)")
@click.option("--targets", help="指定目标文件，逗号分隔 (如 web-01,web-02)")
@click.option("--preview", is_flag=True, help="预览模式，不执行")
def deploy(config_type, targets, preview):
    """部署变更项"""
    changes = detect_changes()
    changes = filter_changes(changes, config_type, targets)

    if not changes:
        click.echo("没有可部署的变更")
        return

    click.echo("\n校验变更项...")
    all_valid = True
    for c in changes:
        valid, errors = validate_change(c)
        if not valid:
            all_valid = False
            click.echo(click.style(f"[ERROR] {c.config_type.value}/{c.name}:", fg="red"))
            for err in errors:
                click.echo(f"       - {err}")

    if not all_valid:
        click.echo(click.style("\n校验失败，请修复上述问题后再试", fg="red"))
        return

    click.echo(click.style("校验通过！", fg="green"))

    # 执行
    results = execute_changes(changes, dry_run=preview)

    click.echo(f"\n执行完成: {results['success']} 成功, {results['failed']} 失败")


@cli.command()
@click.option("--type", "config_type", help="按类型过滤 (hosts/host_groups/services)")
@click.option("--targets", help="指定目标文件，逗号分隔 (如 web-01,web-02)")
def validate(config_type, targets):
    """校验所有变更项的关联关系"""
    changes = detect_changes()
    changes = filter_changes(changes, config_type, targets)

    if not changes:
        click.echo("没有待校验的变更")
        return

    all_valid = True
    for c in changes:
        valid, errors = validate_change(c)
        if valid:
            click.echo(click.style(f"[OK] {c.config_type.value}/{c.name}", fg="green"))
        else:
            all_valid = False
            click.echo(click.style(f"[FAIL] {c.config_type.value}/{c.name}:", fg="red"))
            for err in errors:
                click.echo(f"       - {err}")

    if all_valid:
        click.echo(click.style("\n所有校验通过！", fg="green"))
    else:
        click.echo(click.style("\n校验失败，请修复上述问题", fg="red"))


@cli.command()
@click.argument("change_type")
@click.argument("name")
def show_hook(change_type, name):
    """显示指定类型的 hook 文件路径"""
    from scripts.detector import ConfigType, ChangeType, Change

    try:
        ct = ConfigType(change_type)
    except ValueError:
        click.echo(f"未知类型: {change_type}")
        return

    # 构造一个假的 Change 对象来获取 hook 路径
    fake_change = Change(
        config_type=ct,
        change_type=ChangeType.NEW,
        name=name,
    )
    hook_path = get_hook_path(fake_change)
    click.echo(f"Hook 路径: {hook_path}")
    click.echo(f"存在: {hook_path.exists()}")


def main():
    cli()


if __name__ == "__main__":
    main()
