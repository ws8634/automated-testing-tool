# 自动化测试工具

智能化的自动化测试工具，支持项目结构扫描、关系梳理和测试场景生成。

## 功能特性

- **项目结构扫描**：自动分析本地项目的目录结构和文件组织
- **静态关系分析**：解析类间依赖关系、模块耦合度
- **动态调用关系**：追踪方法调用链、API 调用关系
- **知识图谱生成**：将项目结构可视化为知识图谱或结构化数据
- **E2E 场景生成**：基于项目结构自动生成端到端测试场景说明

## 快速开始

### 安装

```bash
# 从源码安装（推荐开发使用）
git clone https://github.com/ws8634/automated-testing-tool.git
cd automated-testing-tool
pip install -e .

# 或使用 pip
pip install automated-testing-tool
```

### 基础使用

```bash
# 扫描项目结构
automated-test scan /path/to/project

# 生成类间关系图谱（JSON格式）
automated-test analyze --format json --output relations.json

# 生成 Markdown 关系文档
automated-test analyze --format markdown --output relations.md

# 生成 E2E 测试场景
automated-test generate-e2e --output e2e-scenarios.md

# 生成知识图谱（可视化）
automated-test visualize --format html --output graph.html
```

## 项目结构

```
automated_testing_tool/
├── core/                  # 核心模块
│   ├── scanner.py        # 项目扫描器
│   ├── analyzer.py       # 关系分析器
│   └── generator.py      # 场景生成器
├── parsers/              # 代码解析
│   ├── java_parser.py    # Java 代码解析
│   ├── python_parser.py  # Python 代码解析
│   └── js_parser.py      # JavaScript 代码解析
├── exporters/            # 导出模块
│   ├── json_exporter.py  # JSON 导出
│   ├── markdown_exporter.py # Markdown 导出
│   └── graph_exporter.py # 图谱可视化
└── cli.py               # 命令行接口
```

## 作者

ws8634
