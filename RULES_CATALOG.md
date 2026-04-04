# Gatekeeper 内置规则目录

## 规则分类说明

### 1. 高危操作规则 (High-Risk Operations)

| 规则ID | 名称 | 等级 | 说明 |
|--------|------|------|------|
| security-sql-001 | 无 WHERE 条件的 DELETE 语句 | Fatal | 检测可能导致全表数据删除的SQL |
| security-sql-002 | 无 WHERE 条件的 UPDATE 语句 | Fatal | 检测可能导致全表数据更新的SQL |
| security-shell-001 | 危险的 rm -rf 命令 | Fatal | 检测强制递归删除命令 |
| security-permission-001 | 过度宽松的文件权限 | Error | 检测 chmod 777 |

**级联检查示例：**
- `rm -rf` 会级联检查：
  1. 路径限制检查（禁止删除根目录）
  2. 确认步骤检查（是否有用户确认）

### 2. 安全规则 (Security)

| 规则ID | 名称 | 等级 | 说明 |
|--------|------|------|------|
| security-secret-001 | 硬编码密钥或密码 | Error | 检测代码中硬编码的敏感信息 |
| security-injection-001 | SQL 注入风险 | Error | 检测字符串拼接构建的SQL |

**级联检查示例：**
- 硬编码密钥会检查是否使用了环境变量

### 3. 业务规则 (Business)

| 规则ID | 名称 | 等级 | 说明 |
|--------|------|------|------|
| business-auth-001 | 接口权限校验缺失 | Error | 检测缺少权限校验的API接口 |

**级联检查示例：**
- 检查是否添加了权限装饰器（@require_auth等）

### 4. 性能规则 (Performance)

| 规则ID | 名称 | 等级 | 说明 |
|--------|------|------|------|
| performance-db-001 | 潜在的 N+1 查询问题 | Warning | 检测循环中的数据库查询 |

### 5. AI 幻觉规则 (AI Hallucination)

| 规则ID | 名称 | 等级 | 说明 |
|--------|------|------|------|
| ai-hallucination-001 | 可能存在幻觉的 API 调用 | Warning | 检测可能不存在的API调用 |
| ai-hallucination-002 | 逻辑矛盾的代码 | Warning | 检测逻辑矛盾的代码结构 |

**特点：**
- 仅适用于 AI 生成的代码（`ai_code_only: true`）

## 风险等级说明

| 等级 | 说明 | 处理方式 |
|------|------|----------|
| **Fatal** | 致命 | 阻断提交，必须修复 |
| **Error** | 错误 | 需审批后才能提交 |
| **Warning** | 警告 | 仅提示，建议修复 |
| **Info** | 信息 | 仅记录，不阻断 |

## 规则触发条件

每条规则包含以下触发条件：

1. **pattern**: 正则表达式匹配规则
2. **language**: 适用的编程语言
3. **context**: 检测上下文（code/diff/config）
4. **file_pattern**: 适用的文件后缀

## 级联检查 (Cascade Check)

级联检查是 Gatekeeper 的核心特性，用于对高危操作进行深度校验：

### 检查类型

1. **must_contain**: 必须存在的代码模式
   - 示例：DELETE 语句必须包含 WHERE

2. **must_not_contain**: 禁止存在的代码模式
   - 示例：rm -rf 禁止删除根目录

3. **ast_check**: AST节点类型检查（预留）
   - 用于精确的代码结构分析

4. **llm_intent_check**: PRD意图匹配校验（预留）
   - 验证代码是否符合业务需求

### 失败动作

| 动作 | 说明 |
|------|------|
| block | 阻断提交 |
| warn | 仅警告 |
| upgrade_severity | 升级风险等级 |
