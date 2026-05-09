#!/usr/bin/env python3
# 简单的启动脚本
import os
import sys
import subprocess

print("正在启动模拟器...")
print(f"当前目录: {os.getcwd()}")

os.chdir("simulator_v1536")

print(f"切换到目录: {os.getcwd()}")

cmd = ["python", "main.py", "--config", "address_segments_final.txt"]
print(f"执行命令: {' '.join(cmd)}")

try:
    process = subprocess.Popen(cmd, cwd=os.getcwd())
    print("✅ 模拟器启动成功！")
except Exception as e:
    print(f"❌ 启动失败: {e}")
