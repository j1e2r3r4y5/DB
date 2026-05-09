#!/usr/bin/env python3
"""
修复数据库中的变量配置
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
        sql = "SELECT * FROM variables WHERE dev_ID = 30 AND Var_name IN ('9','10','11','12')"
        cursor.execute(sql)
        variables = cursor.fetchall()
        print(f"\n📊 查询到 {len(variables)} 个目标变量:")
        for v in variables:
            print(f"ID={v['ID']} Var_name={v['Var_name']} modbus_addr={v['modbus_addr']} string_len={v['string_len']}")
        return variables

def fix_variable(conn, var_id, correct_addr, correct_string_len):
    """修复单个变量"""
    with conn.cursor() as cursor:
        sql = "UPDATE variables SET modbus_addr = %s, string_len = %s WHERE ID = %s"
        cursor.execute(sql, (correct_addr, correct_string_len, var_id))
        conn.commit()
        print(f"✅ 变量ID={var_id}: 更新modbus_addr={correct_addr}, string_len={correct_string_len}")

def main():
    print("="*60)
    print("修复数据库中的变量配置")
    print("="*60)
    
    conn = connect_db()
    if not conn:
        return
    
    variables = get_variables(conn)
    
    # 定义每个变量的正确配置
    correct_config = {
        '9': {'modbus_addr': '0', 'string_len': '14'},
        '10': {'modbus_addr': '13', 'string_len': '14'},
        '11': {'modbus_addr': '0', 'string_len': '14'},
        '12': {'modbus_addr': '13', 'string_len': '14'},
    }
    
    for v in variables:
        var_name = str(v.get('Var_name', ''))
        if var_name in correct_config:
            print(f"\n🔍 修复变量 {var_name}:")
            config = correct_config[var_name]
            fix_variable(conn, v['ID'], config['modbus_addr'], config['string_len'])
    
    print("\n" + "="*60)
    print("修复完成！让我再次验证...")
    print("="*60)
    
    get_variables(conn)
    
    conn.close()
    print("\n✅ 所有变量配置已修复完成！")

if __name__ == '__main__':
    main()
