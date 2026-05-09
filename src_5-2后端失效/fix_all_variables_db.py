#!/usr/bin/env python3
"""
修复所有变量的配置
"""

import pymysql
from pymysql.cursors import DictCursor

# 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'db': 'device',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}

def connect_db():
    """连接数据库"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print("✅ 数据库连接成功")
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def get_variables(conn):
    """获取所有变量"""
    with conn.cursor() as cursor:
        sql = "SELECT * FROM variables WHERE dev_ID = 30 AND Var_name IN ('1','2','3','4','5','6','7','8','9','10','11','12')"
        cursor.execute(sql)
        variables = cursor.fetchall()
        print(f"\n📊 查询到 {len(variables)} 个变量:")
        for v in variables:
            print(f"ID={v['ID']} Var_name={v['Var_name']} modbus_type={v['modbus_type']} modbus_addr={v['modbus_addr']}")
        return variables

def fix_variable(conn, var_id, correct_addr):
    """修复单个变量"""
    with conn.cursor() as cursor:
        sql = "UPDATE variables SET modbus_addr = %s WHERE ID = %s"
        cursor.execute(sql, (correct_addr, var_id))
        conn.commit()
        print(f"✅ 变量ID={var_id}: 更新modbus_addr={correct_addr}")

def main():
    print("="*60)
    print("修复所有变量的配置")
    print("="*60)
    
    conn = connect_db()
    if not conn:
        return
    
    variables = get_variables(conn)
    
    # 定义每个变量的正确配置
    correct_config = {
        '1': {'modbus_addr': '0'},
        '2': {'modbus_addr': '8'},
        '3': {'modbus_addr': '16'},
        '4': {'modbus_addr': '24'},
        '5': {'modbus_addr': '0'},
        '6': {'modbus_addr': '8'},
        '7': {'modbus_addr': '16'},
        '8': {'modbus_addr': '32'},
        '9': {'modbus_addr': '0'},
        '10': {'modbus_addr': '13'},
        '11': {'modbus_addr': '0'},
        '12': {'modbus_addr': '13'},
    }
    
    for v in variables:
        var_name = str(v.get('Var_name', ''))
        if var_name in correct_config:
            current_addr = str(v.get('modbus_addr', '')) if v.get('modbus_addr') is not None else 'None'
            correct_addr = correct_config[var_name]['modbus_addr']
            if current_addr != correct_addr:
                print(f"\n🔍 修复变量 {var_name}:")
                print(f"  当前: modbus_addr={current_addr}")
                fix_variable(conn, v['ID'], correct_addr)
            else:
                print(f"✅ 变量 {var_name} 正确 (modbus_addr={correct_addr})")
    
    print("\n" + "="*60)
    print("修复完成！再次验证...")
    print("="*60)
    
    get_variables(conn)
    
    conn.close()
    print("\n✅ 所有变量配置已全部修复完成！")

if __name__ == '__main__':
    main()
