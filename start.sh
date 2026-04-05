#!/bin/bash

echo "=== 自动化测试分析器启动脚本 ==="
echo ""

# 检查Python版本
PYTHON_CMD=$(which python3 || which python)
if [ -z "$PYTHON_CMD" ]; then
    echo "错误: 未找到Python解释器"
    exit 1
fi

echo "使用Python: $PYTHON_CMD"
echo ""

# 检查依赖
echo "检查依赖..."
$PYTHON_CMD -c "import flask, flask_cors" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "安装依赖..."
    $PYTHON_CMD -m pip install -r requirements.txt
fi

echo ""
echo "启动服务器..."
echo "访问地址: http://localhost:5000"
echo ""

$PYTHON_CMD app.py
