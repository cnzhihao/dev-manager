# 部署到PyPI指南

## 准备工作

### 1. 注册PyPI账号
访问 https://pypi.org/account/register/ 注册账号

### 2. 配置API Token
1. 登录PyPI后，访问 https://pypi.org/manage/account/token/
2. 创建新的API token（scope选择"Entire account"）
3. 复制生成的token（格式为 `pypi-...`）

### 3. 配置本地认证
```bash
# 方式一：使用keyring（推荐）
keyring set https://upload.pypi.org/legacy/ __token__

# 方式二：创建 ~/.pypirc 文件
cat > ~/.pypirc << EOF
[distutils]
index-servers = pypi

[pypi]
username = __token__
password = pypi-你的token
EOF
chmod 600 ~/.pypirc
```

## 发布流程

### 1. 检查包名可用性
访问 https://pypi.org/project/ai-dev-manager-mcp/ 确认包名未被占用

### 2. 构建包
```bash
python -m build
```

### 3. 检查包内容
```bash
# 检查生成的文件
ls -la dist/

# 验证包内容
tar -tzf dist/ai_dev_manager_mcp-0.1.0.tar.gz
```

### 4. 上传到TestPyPI（可选，用于测试）
```bash
# 上传到测试环境
python -m twine upload --repository testpypi dist/*

# 从测试环境安装验证
pip install --index-url https://test.pypi.org/simple/ ai-dev-manager-mcp
```

### 5. 上传到正式PyPI
```bash
python -m twine upload dist/*
```

### 6. 验证发布
```bash
# 等待几分钟后测试安装
pip install ai-dev-manager-mcp

# 或使用uvx测试
uvx ai-dev-manager-mcp --help
```

## 版本更新流程

### 1. 更新版本号
编辑 `pyproject.toml` 中的 `version` 字段

### 2. 更新变更日志
编辑 `README.md` 或创建 `CHANGELOG.md`

### 3. 重新构建和发布
```bash
# 清理旧的构建文件
rm -rf dist/ build/ *.egg-info/

# 重新构建
python -m build

# 发布新版本
python -m twine upload dist/*
```

## 自动化部署（可选）

### GitHub Actions配置
创建 `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

## 故障排除

### 常见错误

1. **403 Forbidden**: 检查API token是否正确配置
2. **Package already exists**: 版本号已存在，需要更新版本号
3. **Invalid distribution**: 检查 `pyproject.toml` 配置

### 包名冲突
如果 `ai-dev-manager-mcp` 已被占用，可以考虑：
- `ai-dev-manager-tool`
- `smart-dev-manager-mcp`
- `dev-manager-ai-mcp`

### 测试建议
1. 先发布到TestPyPI测试
2. 使用虚拟环境测试安装
3. 测试所有入口点（CLI和MCP服务器）

## 维护建议

1. 遵循语义化版本控制
2. 保持向后兼容性
3. 及时更新依赖包
4. 响应用户Issues和PR 