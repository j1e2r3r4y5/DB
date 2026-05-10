#!/usr/bin/env python3
"""
数据问题诊断工具
帮助定位为什么变量没有数据的问题
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'simulator_v1536'))

import pymysql
import pprint
from datetime import datetime

def check_database_variables():
    """检查数据库中的变量配置"""
    print("="*80)
    print("1. 检查数据库中的变量配置")
    print("="*80)
    
    try:
        conn = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='123456',
            database='ml307_c',
            charset='utf8mb4'
        )
        
        with conn.cursor() as cursor:
            # 查询所有设备
            cursor.execute("SELECT id, dev_serial, dev_name FROM dev")
            devices = cursor.fetchall()
            print(f"\n发现 {len(devices)} 个设备:")
            for dev in devices:
                print(f"  设备ID: {dev[0]}, 序列号: {dev[1]}, 名称: {dev[2]}")
            
            # 查询所有变量
            cursor.execute("""
                SELECT id, dev_id, var_name, data_type, modbus_type, 
                       modbus_device, modbus_addr, data_len, scope
                FROM variables
            """)
            variables = cursor.fetchall()
            print(f"\n发现 {len(variables)} 个变量:")
            for var in variables:
                print(f"  变量ID: {var[0]}, 设备ID: {var[1]}, 名称: {var[2]}")
                print(f"    数据类型: {var[3]}, Modbus类型: {var[4]}, 从站: {var[5]}, 地址: {var[6]}, 长度: {var[7]}, Scope: {var[8]}")
            
            # 查询缓存表
            cursor.execute("SELECT * FROM caching")
            cache_vars = cursor.fetchall()
            print(f"\n缓存表中有 {len(cache_vars)} 个变量:")
            for cv in cache_vars:
                print(f"  {cv}")
        
        conn.close()
        
    except Exception as e:
        print(f"数据库连接失败: {e}")
        print("\n提示：请确保 MySQL 正在运行，且用户名密码正确")

def check_simulator_status():
    """检查模拟器状态"""
    print("\n" + "="*80)
    print("2. 检查模拟器状态")
    print("="*80)
    
    from config import config
    from data.address_segment import AddressSegmentManager, create_default_segments
    
    print(f"\n模拟器配置:")
    print(f"  设备序列号: {config.DEVICE_SERIAL}")
    print(f"  MQTT Broker: {config.MQTT_BROKER}")
    print(f"  上报间隔: {config.HEARTBEAT_INTERVAL}秒")
    
    print(f"\n默认地址段配置:")
    manager = create_default_segments()
    segments = manager._segments
    for seg in segments:
        print(f"  段{seg.segment_id}: 区域{seg.region}, 地址{seg.start_addr}-{seg.start_addr+seg.length-1}, "
              f"名称:{seg.name}, 类型:{seg.data_type}")

def explain_data_flow():
    """解释数据流程"""
    print("\n" + "="*80)
    print("3. 数据流程说明")
    print("="*80)
    
    print("""
数据上传流程：
1. 前端在「变量管理」页面选择变量，点击「下发配置」
2. 后端接收请求，构建功能码0x04，通过MQTT下发给模拟器
3. 模拟器接收配置，保存到 config_manager
4. 模拟器按周期读取 Modbus 数据，构建功能码0x05上报
5. 后端接收功能码0x05，解析数据，调用 ParseAndWriteData
6. 数据写入 InfluxDB

前端数据查询流程：
1. 前端在「数据管理」页面选择设备
2. 前端从数据库读取变量列表
3. 前端按 slave_addr + modbus_type 分组
4. 前端调用 /dataquery 接口查询 InfluxDB
5. 后端从 InfluxDB 查询最新数据返回

常见问题排查：
- 问题1：变量不在活跃列表中？检查 localStorage['activeVariables_{devId}']
- 问题2：modbus_type 不匹配？检查数据库中变量的 modbus_type
- 问题3：数据没有写入 InfluxDB？检查后端日志
- 问题4：数据地址不匹配？检查上报时的 base_addr 和变量的 modbus_addr
    """)

if __name__ == "__main__":
    print("\n" + "="*80)
    print("ML307 数据问题诊断工具")
    print("="*80)
    
    check_database_variables()
    check_simulator_status()
    explain_data_flow()
    
    print("\n" + "="*80)
    print("诊断完成！请检查以上信息")
    print("="*80)
