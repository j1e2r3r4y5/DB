import pymysql
import sys

# 数据库连接
db_config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'device',
    'charset': 'utf8mb4'
}

def check_variables():
    try:
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 查询所有变量
        print("="*80)
        print("所有变量：")
        print("="*80)
        cursor.execute("SELECT * FROM variables")
        all_vars = cursor.fetchall()
        for var in all_vars:
            print(var)
        print(f"\n总计：{len(all_vars)} 个变量\n")
        
        # 查询设备 28 的变量
        print("="*80)
        print("设备 ID 28 的变量：")
        print("="*80)
        cursor.execute("SELECT * FROM variables WHERE dev_id = %s", (28,))
        dev28_vars = cursor.fetchall()
        for var in dev28_vars:
            print(var)
        print(f"\n总计：{len(dev28_vars)} 个变量")
        
        cursor.close()
        connection.close()
        
        return dev28_vars
        
    except Exception as e:
        print(f"数据库连接错误：{e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    check_variables()
