"""
命令行接口
"""

import sys
import os
from typing import Optional

import click
from rich.console import Console

from gatekeeper_agent import __version__
from gatekeeper_agent.rules.loader import load_rules, load_builtin_rules
from gatekeeper_agent.core.scanner import CodeScanner
from gatekeeper_agent.core.report import ReportGenerator
from gatekeeper_agent.utils.logger import setup_logging

console = Console()


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="gatekeeper")
@click.option('--verbose', '-v', is_flag=True, help='启用详细输出')
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """Gatekeeper - AI Guardian Core 静态代码审核工具"""
    if ctx.invoked_subcommand is None:
        # 没有子命令时显示帮助信息
        click.echo(ctx.get_help())
        ctx.exit()
    
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    if verbose:
        setup_logging(level='DEBUG')
    else:
        setup_logging(level='INFO')


@cli.command()
@click.option('--path', '-p', default='.', help='Git 仓库路径')
@click.option('--target', '-t', default='HEAD', help='目标分支或提交')
@click.option('--source', '-s', default=None, help='源分支或提交')
@click.option('--output', '-o', default=None, help='输出报告路径')
@click.option('--format', '-f', 'format_', default='console', 
              type=click.Choice(['console', 'markdown', 'json', 'html']),
              help='报告格式')
@click.option('--no-builtin', is_flag=True, help='不使用内置规则')
@click.option('--rules-dir', '-r', default=None, help='自定义规则目录')
@click.pass_context
def scan(
    ctx: click.Context,
    path: str,
    target: str,
    source: Optional[str],
    output: Optional[str],
    format_: str,
    no_builtin: bool,
    rules_dir: Optional[str]
) -> None:
    """扫描 Git Diff 变更"""
    try:
        # 加载规则
        console.print("[blue]正在加载规则...[/blue]")
        rule_set = load_rules(builtin=not no_builtin, custom_dir=rules_dir)
        console.print(f"[green]已加载 {len(rule_set.rules)} 条规则[/green]")
        
        # 创建扫描器
        scanner = CodeScanner(rule_set)
        
        # 执行扫描
        console.print(f"[blue]正在扫描 Git Diff ({source or 'WORKING'} -> {target})...[/blue]")
        result = scanner.scan_git_diff(
            repo_path=path,
            target=target,
            source=source
        )
        
        # 生成报告
        report_gen = ReportGenerator()
        
        if format_ == 'console':
            report_gen.print_console_report(result)
        elif output:
            saved_path = report_gen.save_report(result, output, format_)
            console.print(f"[green]报告已保存: {saved_path}[/green]")
        else:
            # 输出到控制台
            if format_ == 'markdown':
                console.print(report_gen.generate_markdown(result))
            elif format_ == 'json':
                console.print(report_gen.generate_json(result))
            elif format_ == 'html':
                console.print(report_gen.generate_html(result))
        
        # 根据结果设置退出码
        if result.has_blocking_violations():
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]扫描失败: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--path', '-p', default='.', help='Git 仓库路径')
@click.option('--output', '-o', default=None, help='输出报告路径')
@click.option('--format', '-f', 'format_', default='console',
              type=click.Choice(['console', 'markdown', 'json', 'html']),
              help='报告格式')
@click.option('--no-builtin', is_flag=True, help='不使用内置规则')
@click.option('--rules-dir', '-r', default=None, help='自定义规则目录')
@click.pass_context
def staged(
    ctx: click.Context,
    path: str,
    output: Optional[str],
    format_: str,
    no_builtin: bool,
    rules_dir: Optional[str]
) -> None:
    """扫描暂存区（Staged）变更"""
    try:
        # 加载规则
        console.print("[blue]正在加载规则...[/blue]")
        rule_set = load_rules(builtin=not no_builtin, custom_dir=rules_dir)
        console.print(f"[green]已加载 {len(rule_set.rules)} 条规则[/green]")
        
        # 创建扫描器
        scanner = CodeScanner(rule_set)
        
        # 执行扫描
        console.print("[blue]正在扫描暂存区变更...[/blue]")
        result = scanner.scan_staged(repo_path=path)
        
        # 生成报告
        report_gen = ReportGenerator()
        
        if format_ == 'console':
            report_gen.print_console_report(result)
        elif output:
            saved_path = report_gen.save_report(result, output, format_)
            console.print(f"[green]报告已保存: {saved_path}[/green]")
        else:
            if format_ == 'markdown':
                console.print(report_gen.generate_markdown(result))
            elif format_ == 'json':
                console.print(report_gen.generate_json(result))
            elif format_ == 'html':
                console.print(report_gen.generate_html(result))
        
        if result.has_blocking_violations():
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]扫描失败: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('file_path')
@click.option('--output', '-o', default=None, help='输出报告路径')
@click.option('--format', '-f', 'format_', default='console',
              type=click.Choice(['console', 'markdown', 'json', 'html']),
              help='报告格式')
@click.option('--no-builtin', is_flag=True, help='不使用内置规则')
@click.option('--rules-dir', '-r', default=None, help='自定义规则目录')
@click.pass_context
def file(
    ctx: click.Context,
    file_path: str,
    output: Optional[str],
    format_: str,
    no_builtin: bool,
    rules_dir: Optional[str]
) -> None:
    """扫描单个文件"""
    try:
        # 加载规则
        console.print("[blue]正在加载规则...[/blue]")
        rule_set = load_rules(builtin=not no_builtin, custom_dir=rules_dir)
        console.print(f"[green]已加载 {len(rule_set.rules)} 条规则[/green]")
        
        # 创建扫描器
        scanner = CodeScanner(rule_set)
        
        # 执行扫描
        console.print(f"[blue]正在扫描文件: {file_path}...[/blue]")
        result = scanner.scan_file(file_path)
        
        # 生成报告
        report_gen = ReportGenerator()
        
        if format_ == 'console':
            report_gen.print_console_report(result)
        elif output:
            saved_path = report_gen.save_report(result, output, format_)
            console.print(f"[green]报告已保存: {saved_path}[/green]")
        else:
            if format_ == 'markdown':
                console.print(report_gen.generate_markdown(result))
            elif format_ == 'json':
                console.print(report_gen.generate_json(result))
            elif format_ == 'html':
                console.print(report_gen.generate_html(result))
        
        if result.has_blocking_violations():
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]扫描失败: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('dir_path')
@click.option('--include', '-i', multiple=True, help='包含的文件模式')
@click.option('--exclude', '-e', multiple=True, help='排除的文件模式')
@click.option('--output', '-o', default=None, help='输出报告路径')
@click.option('--format', '-f', 'format_', default='console',
              type=click.Choice(['console', 'markdown', 'json', 'html']),
              help='报告格式')
@click.option('--no-builtin', is_flag=True, help='不使用内置规则')
@click.option('--rules-dir', '-r', default=None, help='自定义规则目录')
@click.pass_context
def directory(
    ctx: click.Context,
    dir_path: str,
    include: tuple,
    exclude: tuple,
    output: Optional[str],
    format_: str,
    no_builtin: bool,
    rules_dir: Optional[str]
) -> None:
    """扫描目录"""
    try:
        # 加载规则
        console.print("[blue]正在加载规则...[/blue]")
        rule_set = load_rules(builtin=not no_builtin, custom_dir=rules_dir)
        console.print(f"[green]已加载 {len(rule_set.rules)} 条规则[/green]")
        
        # 创建扫描器
        scanner = CodeScanner(rule_set)
        
        # 执行扫描
        console.print(f"[blue]正在扫描目录: {dir_path}...[/blue]")
        result = scanner.scan_directory(
            dir_path=dir_path,
            include_patterns=list(include) if include else None,
            exclude_patterns=list(exclude) if exclude else None
        )
        
        # 生成报告
        report_gen = ReportGenerator()
        
        if format_ == 'console':
            report_gen.print_console_report(result)
        elif output:
            saved_path = report_gen.save_report(result, output, format_)
            console.print(f"[green]报告已保存: {saved_path}[/green]")
        else:
            if format_ == 'markdown':
                console.print(report_gen.generate_markdown(result))
            elif format_ == 'json':
                console.print(report_gen.generate_json(result))
            elif format_ == 'html':
                console.print(report_gen.generate_html(result))
        
        if result.has_blocking_violations():
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]扫描失败: {e}[/red]")
        sys.exit(1)


@cli.command()
def rules() -> None:
    """列出所有内置规则"""
    try:
        rule_set = load_builtin_rules()
        
        console.print("[bold blue]Gatekeeper 内置规则列表[/bold blue]\n")
        
        for rule in rule_set.rules:
            severity_color = {
                'fatal': 'red',
                'error': 'orange3',
                'warning': 'yellow',
                'info': 'blue'
            }.get(rule.severity.value, 'white')
            
            console.print(f"[bold]{rule.name}[/bold] [{severity_color}]({rule.severity.value.upper()})[/{severity_color}]")
            console.print(f"  ID: {rule.rule_id}")
            console.print(f"  分类: {rule.category.value}")
            console.print(f"  描述: {rule.description}")
            console.print(f"  启用: {'是' if rule.enabled else '否'}")
            if rule.metadata.ai_code_only:
                console.print(f"  [dim]仅适用于 AI 生成代码[/dim]")
            console.print()
            
    except Exception as e:
        console.print(f"[red]加载规则失败: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', default='gatekeeper-report.html', help='输出文件路径')
def init_hooks(output: str) -> None:
    """初始化 Git Hooks"""
    try:
        hook_content = f'''#!/bin/bash
# Gatekeeper Pre-commit Hook
# 自动生成，请勿手动修改

echo "🔒 Gatekeeper 正在审核代码..."

# 运行 gatekeeper 检查暂存区
gatekeeper staged --format console

# 检查退出码
if [ $? -ne 0 ]; then
    echo "❌ Gatekeeper 检测到阻断性问题，提交被拒绝"
    echo "请修复问题后再次提交"
    exit 1
fi

echo "✅ Gatekeeper 审核通过"
exit 0
'''
        
        # 查找 Git 仓库
        git_dir = os.path.join(os.getcwd(), '.git')
        if not os.path.exists(git_dir):
            console.print("[red]错误: 当前目录不是 Git 仓库[/red]")
            sys.exit(1)
        
        hooks_dir = os.path.join(git_dir, 'hooks')
        pre_commit_hook = os.path.join(hooks_dir, 'pre-commit')
        
        # 写入 hook
        with open(pre_commit_hook, 'w') as f:
            f.write(hook_content)
        
        # 设置可执行权限
        os.chmod(pre_commit_hook, 0o755)
        
        console.print(f"[green]✅ Pre-commit Hook 已安装: {pre_commit_hook}[/green]")
        console.print("[dim]现在每次 git commit 都会自动运行 Gatekeeper 审核[/dim]")
        
    except Exception as e:
        console.print(f"[red]安装 Hook 失败: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--port', '-p', default=8080, help='Web 服务端口')
@click.option('--host', '-h', default='127.0.0.1', help='Web 服务主机')
@click.option('--no-open', is_flag=True, help='不自动打开浏览器')
def web(port: int, host: str, no_open: bool) -> None:
    """启动 Web 管理界面"""
    try:
        from gatekeeper_agent.web import start_server
        
        console.print(f"[bold blue]启动 Gatekeeper Web 管理界面...[/bold blue]")
        console.print(f"[dim]服务地址: http://{host}:{port}[/dim]\n")
        
        # 尝试自动打开浏览器
        if not no_open:
            import webbrowser
            import threading
            import time
            
            def open_browser():
                time.sleep(1.5)
                webbrowser.open(f"http://{host}:{port}")
            
            threading.Thread(target=open_browser, daemon=True).start()
        
        start_server(port=port, host=host)
        
    except ImportError as e:
        console.print(f"[red]启动失败: 缺少 Web 依赖[/red]")
        console.print("[dim]请安装 Web 依赖: pip install -e '.[web]'[/dim]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]启动 Web 服务失败: {e}[/red]")
        sys.exit(1)


def main() -> None:
    """主入口"""
    cli()


if __name__ == '__main__':
    main()
