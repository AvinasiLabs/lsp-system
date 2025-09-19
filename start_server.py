#!/usr/bin/env python3
"""
启动LSP积分系统API服务器
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    print("🚀 启动LSP积分系统API服务器...")
    print("📚 API文档地址: http://localhost:12001/lsp/docs")
    print("📊 ReDoc文档: http://localhost:12001/lsp/redoc")
    print("💡 按 Ctrl+C 停止服务器\n")
    
    main()