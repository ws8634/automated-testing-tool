#!/bin/bash

# 安装依赖
pip install -r requirements.txt

# 启动后端服务器
echo "Starting backend server..."
python src/api/app.py