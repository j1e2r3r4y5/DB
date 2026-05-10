#!/usr/bin/env python3
"""
检查表结构
"""
import pymysql

def check_tables():
    print("="*80)
    print("检查数据库表结构")
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
            # 查看所有表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"\n数据库中的表:")
            for table in tables:
                print(f"  - {table[0]}")
            
            # 查看 variables 表结构
            print(f"\nvariables 表结构:")
            cursor.execute("DESCRIBE variables")
            for col in cursor.fetchall():
                print(f"  {col[0]} - {col[1]}")
            
            # 查看 caching 表结构
            print(f"\ncaching 表结构:")
            cursor.execute("DESCRIBE caching")
            for col in cursor.fetchall():
                print(f"  {col[0]} - {col[1]}")
            
            # 查看 variables 表数据
            print(f"\nvariables 表数据:")
            cursor.execute("SELECT * FROM variables LIMIT 10")
            cols = [desc[0] for desc in cursor.description]
            print(f"  列: {cols}")
            for row in cursor.fetchall():
                print(f"  {row}")
            
            # 查看 caching 表数据
            print(f"\ncaching 表数据:")
            cursor.execute("SELECT * FROM caching LIMIT 10")
            cols = [desc[0] for desc in cursor.description]
            print(f"  列: {cols}")
            for row in cursor.fetchall():
                print(f"  {row}")
            
        conn.close()
        print("\n✅ 表结构检查完成")
        
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_tables()
