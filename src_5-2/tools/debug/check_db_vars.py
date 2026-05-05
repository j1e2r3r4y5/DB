
#!/usr/bin/env python3
import pymysql
import json

# 数据库配置
config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'device',
    'charset': 'utf8mb4',
}

def main():
    print("="*60)
    print("查询数据库里的变量")
    print("="*60)
    
    # 连接数据库
    try:
        conn = pymysql.connect(**config)
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return
    
    try:
        # 查询variables表
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 查询所有变量
            cursor.execute("SELECT * FROM variables")
            variables = cursor.fetchall()
            print(f"\n📋 找到 {len(variables)} 个变量\n")
            
            for var in variables:
                print("-" * 60)
                print(f"变量名称: {var['Var_name']}")
                print(f"设备ID: {var['dev_ID']}")
                print(f"数据类型: {var['Data_type']} (DataType)")
                print(f"Modbus类型: {var['modbus_type']} (ModbusType)")
                print(f"Modbus从站: {var['modbus_device']}")
                print(f"Modbus地址: {var['modbus_addr']}")
                print(f"数据长度: {var['data_len']}")
                print(f"字符串长度: {var['string_len']}")
                print(f"小数位数: {var['Decimal_digits']}")
        
        # 查询caching表
        print("\n" + "="*60)
        print("查询缓存表 (caching)")
        print("="*60)
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM caching")
            caches = cursor.fetchall()
            print(f"\n📋 找到 {len(caches)} 条缓存记录\n")
            
            for cache in caches:
                print("-" * 60)
                print(f"变量名称: {cache['Var_name']}")
                print(f"设备ID: {cache['DevID']}")
                print(f"数据类型: {cache['DataType']}")
                print(f"Modbus类型: {cache['ModbusType']}")
                print(f"Modbus从站: {cache['ModbusDevice']}")
                print(f"Modbus地址: {cache['ModbusAddr']}")
                print(f"数据长度: {cache['DataLen']}")
                print(f"字符串长度: {cache['StringLen']}")
                
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        print("\n✅ 数据库连接已关闭")

if __name__ == "__main__":
    main()
