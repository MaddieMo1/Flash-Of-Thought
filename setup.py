#!/usr/bin/env python3
"""
FlashOfThought 项目安装脚本
用于自动化项目初始化和依赖安装
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """运行命令并显示进度"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ 是必需的")
        return False
    print(f"✅ Python {sys.version.split()[0]} 符合要求")
    return True

def install_dependencies():
    """安装项目依赖"""
    print("📚 安装项目依赖...")
    return run_command("pip install -r requirements.txt", "安装依赖包")

def create_directories():
    """创建必要的目录"""
    print("📁 创建项目目录...")
    directories = [
        "static/uploads",
        "data/chroma_db", 
        "logs",
        "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {directory}")
    
    return True

def create_env_file():
    """创建环境配置文件"""
    env_file = ".env"
    example_file = ".env.example"
    
    if not os.path.exists(env_file):
        if os.path.exists(example_file):
            print("📝 从模板创建 .env 文件...")
            with open(example_file, 'r') as f:
                content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print("✅ .env 文件已创建，请编辑并填入实际配置值")
        else:
            print("⚠️  .env.example 模板文件不存在")
            return False
    else:
        print("✅ .env 文件已存在")
    
    return True

def main():
    """主安装流程"""
    print("🚀 FlashOfThought 项目安装开始...")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 创建目录
    if not create_directories():
        sys.exit(1)
    
    # 创建环境文件
    if not create_env_file():
        sys.exit(1)
    
    # 安装依赖
    if not install_dependencies():
        print("⚠️  依赖安装失败，请手动运行: pip install -r requirements.txt")
    
    print("\n" + "=" * 50)
    print("🎉 安装完成！")
    print("\n下一步:")
    print("1. 编辑 .env 文件，填入阿里云OSS和DashScope配置")
    print("2. 启动后端服务: uvicorn app.main:app --reload")
    print("3. 启动前端界面: streamlit run ui/app.py")
    print("\n📖 更多信息请查看 README.md")

if __name__ == "__main__":
    main()