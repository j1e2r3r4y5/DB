#!/usr/bin/env python3
"""
快速诊断检查工具
"""
import pymysql
import sys

def check_mysql():
    print("="*80)
    print("检查 MySQL 数据库")
    print("="*80)
    
    try:
        conn = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='123456',
            database='device',
            charset='utf8mb4'
        )
        
        with conn.cursor() as cursor:
            # 检查设备
            cursor.execute("SELECT id, DevSerial, DevName, Changeflag FROM dev")
            devices = cursor.fetchall()
            print(f"\n设备列表:")
            for dev in devices:
                print(f"  ID: {dev[0]}, Serial: {dev[1]}, Name: {dev[2]}, Changeflag: {dev[3]}")
            
            # 检查变量
            if devices:
                dev_id = devices[0][0]
                cursor.execute("""
                    SELECT id, VarName, DataType, ModbusType, ModbusDevice, ModbusAddr, DataLen, scope 
                    FROM variables WHERE DevID = %s
                """, (dev_id,))
                variables = cursor.fetchall()
                print(f"\n变量列表 (设备ID={dev_id}):")
                for var in variables:
                    print(f"  ID: {var[0]}, Name: {var[1]}, Type: {var[2]}, "
                          f"ModbusType: {var[3]}, Slave: {var[4]}, Addr: {var[5]}, "
                          f"Len: {var[6]}, Scope: {var[7]}")
                
                # 检查缓存表
                cursor.execute("""
                    SELECT id, VarName, DataType, ModbusType, ModbusDevice, ModbusAddr, DataLen 
                    FROM caching WHERE DevID = %s
                """, (dev_id,))
                caching = cursor.fetchall()
                print(f"\n缓存表 (设备ID={dev_id}):")
                if caching:
                    for var in caching:
                        print(f"  ID: {var[0]}, Name: {var[1]}, Type: {var[2]}, "
                              f"ModbusType: {var[3]}, Slave: {var[4]}, Addr: {var[5]}, Len: {var[6]}")
                else:
                    print("  (空！缓存表没有数据！)")
            
        conn.close()
        print("\n✅ MySQL 检查完成")
        
    except Exception as e:
        print(f"\n❌ MySQL 连接失败: {e}")
        print("  请检查 MySQL 是否正在运行，用户名密码是否正确")

def main():
    print("\n" + "="*80)
    print("ML307 快速诊断工具")
    print("="*80)
    
    check_mysql()
    
    print("\n" + "="*80)
    print("下一步建议：")
    print("  1. 查看后端控制台日志，看有没有数据上报")
    print("  2. 查看模拟器控制台日志，看有没有收到下发和上报数据")
    print("  3. 如果缓存表为空，请先在变量管理页面勾选变量并重新下发")
    print("="*80)

if __name__ == "__main__":
    main()
