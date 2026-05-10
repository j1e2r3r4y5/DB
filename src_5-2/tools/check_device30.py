#!/usr/bin/env python3
"""
检查设备 30 的详细状态
"""
import pymysql

def check_device30():
    print("="*80)
    print("检查设备 ID=30 的状态")
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
            # 查看设备信息
            cursor.execute("SELECT * FROM dev WHERE id = 30")
            dev = cursor.fetchone()
            if dev:
                cols = [desc[0] for desc in cursor.description]
                print(f"\n设备信息:")
                for col, val in zip(cols, dev):
                    print(f"  {col}: {val}")
            
            # 查看该设备的所有变量
            print(f"\n该设备的变量:")
            cursor.execute("SELECT * FROM variables WHERE dev_ID = 30")
            variables = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            print(f"  列: {cols}")
            for var in variables:
                print(f"\n  变量:")
                for col, val in zip(cols, var):
                    print(f"    {col}: {val}")
            
            # 查看缓存表
            print(f"\n缓存表中的数据 (dev_ID=30):")
            cursor.execute("SELECT * FROM caching WHERE dev_ID = 30")
            caching = cursor.fetchall()
            if caching:
                cols = [desc[0] for desc in cursor.description]
                print(f"  列: {cols}")
                for var in caching:
                    print(f"\n  缓存变量:")
                    for col, val in zip(cols, var):
                        print(f"    {col}: {val}")
            else:
                print("  (空！缓存表中没有该设备的数据！)")
            
        conn.close()
        
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_device30()
