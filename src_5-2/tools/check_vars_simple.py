#!/usr/bin/env python3
"""
简单检查变量表
"""
import pymysql

def check_vars():
    print("="*80)
    print("检查变量表")
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
            # 检查生产环境的变量
            print("\n生产环境变量 (scope != 'sandbox'):")
            cursor.execute("""
                SELECT id, dev_ID, Var_name, Data_type, modbus_type, 
                       modbus_device, modbus_addr, data_len, scope
                FROM variables 
                WHERE dev_ID = 30 AND scope != 'sandbox'
            """)
            vars = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            print(f"列: {cols}")
            for v in vars:
                print(f"\n变量:")
                for c, val in zip(cols, v):
                    print(f"  {c}: {val}")
            
            # 检查缓存表
            print("\n\n缓存表:")
            cursor.execute("""
                SELECT id, dev_ID, Var_name, Data_type, modbus_type, 
                       modbus_device, modbus_addr, data_len, scope
                FROM caching 
                WHERE dev_ID = 30
            """)
            cache = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            print(f"列: {cols}")
            for v in cache:
                print(f"\n缓存:")
                for c, val in zip(cols, v):
                    print(f"  {c}: {val}")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_vars()
