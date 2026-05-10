#!/usr/bin/env python3
"""
检查所有变量
"""
import pymysql

def check_vars():
    print("="*80)
    print("检查设备 30 的所有变量")
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
            # 检查该设备的所有变量
            print("\nvariables 表中的所有变量:")
            cursor.execute("""
                SELECT id, dev_ID, Var_name, Data_type, modbus_type, 
                       modbus_device, modbus_addr, scope
                FROM variables 
                WHERE dev_ID = 30
            """)
            vars = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            print(f"共 {len(vars)} 个变量")
            for v in vars:
                scope = v[7] if v[7] else 'production'
                scope_label = '🧪 沙箱' if scope == 'sandbox' else '📦 生产'
                print(f"  [{scope_label}] id={v[0]}, name={v[2]}, type={v[4]}, addr={v[6]}")
            
        conn.close()
        
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_vars()
