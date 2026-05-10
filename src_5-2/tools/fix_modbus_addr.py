#!/usr/bin/env python3
"""
修复 variables 表中的 modbus_addr 字段
从 caching 表同步
"""
import pymysql

def fix_modbus_addr():
    print("="*80)
    print("修复 variables 表的 modbus_addr")
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
            # 查询需要修复的变量
            print("\n查询 variables 表中 modbus_addr 为 NULL 的记录:")
            cursor.execute("""
                SELECT id, dev_ID, Var_name, modbus_type, modbus_device
                FROM variables 
                WHERE modbus_addr IS NULL
            """)
            vars = cursor.fetchall()
            print(f"找到 {len(vars)} 条记录需要修复")
            
            for v in vars:
                var_id, dev_id, var_name, mtype, mdevice = v
                print(f"\n  变量 {var_name} (id={var_id}):")
                
                # 从 caching 表查找对应的记录
                cursor.execute("""
                    SELECT modbus_addr
                    FROM caching 
                    WHERE dev_ID = %s 
                      AND modbus_type = %s 
                      AND modbus_device = %s
                    LIMIT 1
                """, (dev_id, mtype, mdevice))
                cache = cursor.fetchone()
                
                if cache:
                    cache_addr = cache[0]
                    print(f"    从 caching 表找到 modbus_addr = {cache_addr}")
                    
                    # 更新 variables 表
                    cursor.execute("""
                        UPDATE variables 
                        SET modbus_addr = %s 
                        WHERE id = %s
                    """, (cache_addr, var_id))
                    print(f"    ✅ 已更新")
                else:
                    print(f"    ❌ caching 表中未找到对应记录")
            
            # 提交事务
            conn.commit()
            
            # 验证修复结果
            print("\n\n验证修复结果:")
            cursor.execute("""
                SELECT id, dev_ID, Var_name, modbus_type, modbus_device, modbus_addr
                FROM variables 
                WHERE dev_ID = 30 AND scope != 'sandbox'
            """)
            result = cursor.fetchall()
            for r in result:
                print(f"  变量 {r[2]}: modbus_addr = {r[5]}")
        
        conn.close()
        print("\n✅ 修复完成！")
        
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_modbus_addr()
