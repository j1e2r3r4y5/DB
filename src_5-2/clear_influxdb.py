#!/usr/bin/env python3
"""
清空 InfluxDB 历史数据脚本
"""
import requests
import json

# InfluxDB配置
INFLUX_URL = "http://localhost:8086"
ORG = "iot"  # 根据实际配置修改
BUCKET = "iot_bucket"  # 根据实际配置修改
TOKEN = "687b6d1952ef7f7bc0d209a3d498694b1f55d3d51f0a49de63093e6c307c0b7d"  # 如果有认证需要填

def clear_influxdb():
    print("=" * 60)
    print("      🚀 开始清空 InfluxDB 历史数据")
    print("=" * 60)
    
    # 方法1：尝试直接删除数据（使用 InfluxDB API v2）
    try:
        # 先测试连接
        print(f"\n📡 尝试连接 InfluxDB: {INFLUX_URL}")
        test_res = requests.get(f"{INFLUX_URL}/health", timeout=5)
        print(f"✅ InfluxDB 状态: {test_res.status_code}")
    except Exception as e:
        print(f"⚠️  无法连接 InfluxDB: {e}")
        print("\n💡 请手动清空 InfluxDB：")
        print("   1. 打开浏览器访问: http://localhost:8086")
        print("   2. 登录后进入 Data Explorer")
        print("   3. 删除 bucket 中的数据，或重新创建 bucket")
        print("\n或者简单重启 InfluxDB 也行！")
        return False
    
    print("\n" + "=" * 60)
    print("      ✅ 请在前端进行以下操作：")
    print("=" * 60)
    print("\n1️⃣  打开浏览器访问: http://localhost:4326")
    print("2️⃣  登录（admin / 1）")
    print("3️⃣  进入「设备管理」")
    print("4️⃣  选中「ML307测试设备」")
    print("5️⃣  点击「配置下发」")
    print("6️⃣  然后进入「设备列表」→「查看数据」")
    print("\n🔍 检查后端日志看数据解析是否正确！")
    
    return True

if __name__ == "__main__":
    clear_influxdb()
