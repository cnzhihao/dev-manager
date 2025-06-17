#!/bin/bash

# AI开发经理MCP包发布脚本
# 使用方法: ./publish.sh [test|prod]

set -e

MODE=${1:-"test"}

echo "🚀 开始发布AI开发经理MCP包..."

# 检查必要的工具
if ! command -v python &> /dev/null; then
    echo "❌ Python未安装"
    exit 1
fi

if ! python -m pip show build &> /dev/null; then
    echo "📦 安装构建工具..."
    pip install build twine
fi

# 清理旧的构建文件
echo "🧹 清理旧的构建文件..."
rm -rf dist/ build/ *.egg-info/

# 构建包
echo "🔨 构建Python包..."
python -m build

# 检查包内容
echo "📋 检查生成的文件:"
ls -la dist/

# 验证包
echo "✅ 验证包结构..."
python -m twine check dist/*

if [ "$MODE" = "test" ]; then
    echo "🧪 上传到TestPyPI..."
    echo "请确保已配置TestPyPI认证信息"
    python -m twine upload --repository testpypi dist/*
    
    echo "✅ 上传完成！"
    echo "🔗 查看包: https://test.pypi.org/project/ai-dev-manager-mcp/"
    echo "📦 安装测试: pip install --index-url https://test.pypi.org/simple/ ai-dev-manager-mcp"
    
elif [ "$MODE" = "prod" ]; then
    echo "🌟 上传到正式PyPI..."
    echo "请确保已配置PyPI认证信息"
    
    read -p "确认发布到正式PyPI? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python -m twine upload dist/*
        
        echo "🎉 发布成功！"
        echo "🔗 查看包: https://pypi.org/project/ai-dev-manager-mcp/"
        echo "📦 安装命令: pip install ai-dev-manager-mcp"
        echo "🚀 uvx命令: uvx ai-dev-manager-mcp --help"
    else
        echo "❌ 发布已取消"
        exit 1
    fi
else
    echo "❌ 无效的模式: $MODE"
    echo "使用方法: ./publish.sh [test|prod]"
    exit 1
fi

echo "🎊 完成！" 