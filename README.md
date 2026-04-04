# Gatekeeper Agent - AI Guardian Core

AI 驱动的代码审核系统，守护代码质量与安全。

## 功能特性

- **高危操作拦截**：rm -rf、无 WHERE 的 DELETE/UPDATE 等
- **安全漏洞检测**：硬编码密钥、SQL 注入、XSS 等
- **供应链安全**：基于 OpenClaw 安全建议的防护规则
- **业务规则校验**：支付接口、权限控制等
- **性能问题识别**：N+1 查询、内存泄漏等
- **幻觉代码检测**：不存在的 API、逻辑矛盾、冗余代码
- **意图一致性**：关联 PRD 文本校验

## 快速开始

### 安装

```bash
# 从源码安装（推荐开发使用）
git clone https://github.com/aiguardian/gatekeeper-agent.git
cd gatekeeper-agent
pip install -e .

# 或使用 pip
pip install gatekeeper-agent
```

### 基础使用

```bash
# 显示帮助信息
gk

# 显示版本
gk --version

# 扫描暂存区（Git Staged）
gatekeeper staged

# 扫描 Git Diff
gatekeeper scan --target HEAD

# 扫描单个文件
gatekeeper file path/to/file.py

# 扫描目录
gatekeeper directory path/to/src

# 生成 HTML 报告
gatekeeper staged --format html --output report.html

# 生成 Markdown 报告
gatekeeper scan --format markdown --output report.md

# 生成 JSON 报告（适合 CI/CD）
gatekeeper scan --format json --output report.json

# 启用详细输出模式
gatekeeper -v scan
gatekeeper --verbose rules
```

### 初始化 Git Hook

```bash
# 安装 Pre-commit Hook
gatekeeper init-hooks

# 现在每次 git commit 都会自动运行代码审核
# 如果检测到阻断性违规，提交会被阻止
```

### Web 管理界面

Gatekeeper 提供可视化的 Web 管理界面，方便规则管理和报告查看。

#### 启动 Web 服务

```bash
# 启动 Web 界面（默认 http://127.0.0.1:8080）
gatekeeper web

# 指定端口和主机（允许局域网访问）
gatekeeper web --host 0.0.0.0 --port 8080

# 不自动打开浏览器
gatekeeper web --no-open
```

#### Web 界面功能

| 功能模块 | 说明 |
|----------|------|
| **Dashboard** | 规则统计、风险分布、快速操作 |
| **规则管理** | 查看规则列表、启用/禁用规则、新建自定义规则 |
| **扫描任务** | 创建扫描任务、查看实时结果、保存报告、删除任务 |
| **报告中心** | 查看扫描报告、导出报告、删除报告 |

#### 扫描类型说明

| 类型 | 说明 | 使用场景 |
|------|------|----------|
| **Staged** | 扫描 Git 暂存区（已 `git add` 但未提交的文件） | 提交前检查 |
| **Diff** | 扫描 Git 差异（两个提交/分支之间的变更） | 对比版本 |
| **Directory** | 扫描指定目录 | 完整项目扫描 |
| **File** | 扫描单个文件 | 快速检查 |

#### 报告管理

- **扫描任务页面**：扫描完成后，可以手动"保存报告"到报告中心
- **报告中心**：查看、导出（HTML/JSON）、删除报告
- **默认存储**：报告默认保存在内存中，重启后清空

#### Web 界面配置

```bash
# 配置报告保存路径（默认：~/.gatekeeper/reports）
export GATEKEEPER_REPORT_PATH=/path/to/reports

# 配置服务器主机和端口
export GATEKEEPER_WEB_HOST=0.0.0.0
export GATEKEEPER_WEB_PORT=8080

# 启动服务
gatekeeper web
```

#### 首次使用 Web 界面

```bash
# 1. 安装 Web 依赖（首次需要）
pip install -e ".[web]"

# 2. 构建前端（首次需要）
cd gatekeeper_agent/web/frontend
npm install
npm run build
cd ../../..

# 3. 启动服务
gatekeeper web --host 0.0.0.0

# 4. 浏览器访问 http://localhost:8080
```

## 项目结构

```
gatekeeper_agent/
├── web/                    # Web 界面模块
│   ├── backend/           # FastAPI 后端
│   └── frontend/          # Vue3 前端
├── core/                  # 核心模块
│   ├── engine.py         # 规则引擎
│   ├── scanner.py        # 代码扫描器
│   └── report.py         # 报告生成器
├── rules/                 # 规则管理
│   ├── builtin/          # 内置规则
│   │   ├── high_risk.py      # 高危操作规则
│   │   ├── security.py       # 安全规则
│   │   ├── supply_chain.py   # 供应链安全规则
│   │   ├── business.py       # 业务规则
│   │   ├── performance.py    # 性能规则
│   │   ├── ai_hallucination.py # AI幻觉规则
│   │   └── style.py          # 代码规范规则
│   └── loader.py         # 规则加载器
├── models/               # 数据模型
│   ├── rule.py          # 规则模型
│   └── scan.py          # 扫描结果模型
├── parsers/              # 代码解析
│   ├── git_parser.py    # Git 解析
│   └── file_parser.py   # 文件解析
├── utils/                # 工具模块
│   └── logger.py        # 日志配置
└── cli.py               # 命令行接口
```

## 内置规则目录

### 规则分类与严重级别

Gatekeeper 采用四级严重级别体系：

| 级别 | 颜色 | 处理方式 | 说明 |
|------|------|----------|------|
| **FATAL** | 🔴 红色 | **阻断提交** | 高危操作，必须修复 |
| **ERROR** | 🟠 橙色 | **需审批** | 安全问题，需要安全团队审批 |
| **WARNING** | 🟡 黄色 | **仅提示** | 潜在风险，建议修复 |
| **INFO** | 🔵 蓝色 | **仅记录** | 规范建议，不阻断 |

### 1. 高危操作规则 (high_risk)

**FATAL 级别（阻断提交）：**

| 规则ID | 名称 | 描述 |
|--------|------|------|
| `security-sql-001` | 无 WHERE 条件的 DELETE 语句 | 可能导致全表数据被删除 |
| `security-sql-002` | 无 WHERE 条件的 UPDATE 语句 | 可能导致全表数据被更新 |
| `security-shell-001` | 危险的文件删除命令 | `rm -rf` 强制删除且无法恢复 |
| `security-shell-003` | 危险的磁盘操作命令 | `dd` 直接操作磁盘设备 |
| `security-shell-004` | 危险的文件系统格式化命令 | `mkfs` 格式化磁盘分区 |

**ERROR 级别（需审批）：**

| 规则ID | 名称 | 描述 |
|--------|------|------|
| `security-shell-002` | 无限制的 sudo 命令 | 以 root 权限执行危险操作 |
| `security-k8s-001` | 危险的 Kubernetes 删除命令 | `kubectl delete` 删除生产资源 |
| `security-docker-001` | 危险的 Docker 强制操作 | `docker rm -f` 强制删除容器 |

### 2. 安全规则 (security)

**FATAL 级别（阻断提交）：**

| 规则ID | 名称 | 描述 |
|--------|------|------|
| `security-secret-004` | 私钥文件内容检测 | RSA/SSH/SSL 私钥绝对不允许提交 |

**ERROR 级别（需审批）：**

| 规则ID | 名称 | 描述 |
|--------|------|------|
| `security-secret-001` | 硬编码密钥或密码 | 生产环境密钥硬编码 |
| `security-secret-002` | 测试环境密钥硬编码 | 测试环境配置建议统一管理 |
| `security-injection-001` | SQL 注入风险 | 字符串拼接构建 SQL 查询 |
| `security-permission-001` | 过度宽松的文件权限 | `chmod 777` 全开放权限 |
| `security-permission-002` | 敏感文件权限暴露 | `.env` 等敏感文件权限不当 |
| `security-cors-001` | 过于宽松的 CORS 配置 | 允许任意来源 `*` |

**WARNING 级别（仅提示）：**

| 规则ID | 名称 | 描述 |
|--------|------|------|
| `security-secret-003` | 配置文件中的敏感字段 | YAML/JSON 中的明文密码 |
| `security-log-001` | 敏感信息日志打印 | 日志中输出密码、密钥等 |

**INFO 级别（仅记录）：**

| 规则ID | 名称 | 描述 |
|--------|------|------|
| `security-config-001` | 调试模式启用 | `DEBUG=True` 生产环境风险 |

### 3. 供应链安全规则 (supply_chain)

基于 [OpenClaw 安全建议](https://mp.weixin.qq.com/s/ZeUVMgYUlkpioGGg2Oilzw) 实现：

| 规则ID | 名称 | 级别 | 描述 |
|--------|------|------|------|
| `supply-chain-001` | 远程脚本下载执行风险 | **FATAL** | `curl/wget | bash` 模式 |
| `supply-chain-002` | 动态代码执行风险 | **ERROR** | `eval/exec` 代码注入 |
| `supply-chain-003` | Base64 解码执行风险 | **ERROR** | Base64 隐藏恶意代码 |
| `supply-chain-004` | 危险的管道命令组合 | **ERROR** | `curl | sudo` 等危险组合 |

### 4. 业务规则 (business)

| 规则ID | 名称 | 级别 | 描述 |
|--------|------|------|------|
| `business-auth-001` | 接口权限校验缺失 | **ERROR** | 缺少权限校验的接口定义 |

### 5. 性能规则 (performance)

| 规则ID | 名称 | 级别 | 描述 |
|--------|------|------|------|
| `performance-db-001` | 潜在的 N+1 查询问题 | **WARNING** | 循环中存在数据库查询 |

### 6. AI 幻觉规则 (ai_hallucination)

| 规则ID | 名称 | 级别 | 描述 |
|--------|------|------|------|
| `ai-hallucination-001` | 可能存在幻觉的 API 调用 | **WARNING** | 不存在的 API 或方法 |
| `ai-hallucination-002` | 逻辑矛盾的代码 | **WARNING** | 条件判断矛盾、不可达代码 |

### 7. 代码规范规则 (style)

| 规则ID | 名称 | 级别 | 描述 |
|--------|------|------|------|
| `style-docstring-001` | 公共函数缺少文档字符串 | **INFO** | 函数/类缺少文档说明 |
| `style-comment-001` | 复杂逻辑建议添加注释 | **INFO** | 嵌套循环等复杂逻辑 |
| `style-todo-001` | 代码中包含 TODO 标记 | **INFO** | TODO/FIXME/XXX 标记 |

## 配置说明

### 环境变量

```bash
# 指定自定义规则目录
export GATEKEEPER_RULES_DIR=/path/to/custom/rules

# 设置日志级别（DEBUG/INFO/WARNING/ERROR）
export GATEKEEPER_LOG_LEVEL=INFO

# Web 界面配置
export GATEKEEPER_REPORT_PATH=~/.gatekeeper/reports
export GATEKEEPER_WEB_HOST=127.0.0.1
export GATEKEEPER_WEB_PORT=8080
```

### 自定义规则

Gatekeeper 支持通过 YAML 文件添加自定义规则：

```yaml
# 自定义规则示例 .gatekeeper/rules/my-rules.yaml
name: "团队自定义规则"
description: "业务特定的代码规范"
version: "1.0.0"
rules:
  - rule_id: "custom-001"
    name: "禁止直接调用生产 API"
    severity: "error"
    category: "business"
    description: "测试代码中不应直接调用生产环境 API"
    triggers:
      - pattern: "api\.production\.example\.com"
        language: ["python", "javascript"]
        file_pattern: ["*.py", "*.js"]
    violation_response:
      block_commit: false
      message: "检测到生产 API 调用，请使用测试环境配置"
      suggested_fix: "api.test.example.com"
```

## 开发指南

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black gatekeeper_agent/
isort gatekeeper_agent/
```

### 类型检查

```bash
mypy gatekeeper_agent/
```

## Agent 改造分析

关于是否将 Gatekeeper 从传统规则引擎改造为智能 Agent 的详细分析，请参阅 [AGENT_TRANSFORMATION_ANALYSIS.md](AGENT_TRANSFORMATION_ANALYSIS.md)。

**核心结论：**
- 当前采用**纯规则引擎**方案，确定性高、可解释性强
- 推荐未来采用**规则 + LLM 辅助**的混合方案
- 不建议完全依赖 LLM，因为代码审核需要 100% 确定性

## 版本说明

当前版本：**0.1.0**

版本号格式遵循 X.Y.Z：
- **X (0)**：大的发布版本（当前为 Alpha 阶段）
- **Y (1)**：项目内部研发定义版本
- **Z (0)**：当前修改版本

## License

MIT License

---

**作者**: 王森  
**创建时间**: 2026-03-14  
**项目愿景**: 构建 AI 研发全流程的质量第一道防线
