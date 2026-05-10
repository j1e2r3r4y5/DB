#!/usr/bin/env python3
"""
直接查询 InfluxDB 检查数据
"""
import sys
from datetime import datetime, timedelta

try:
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.write_api import SYNCHRONOUS
except ImportError:
    print("需要安装 influxdb_client: pip install influxdb-client")
    sys.exit(1)

def check_influx():
    print("="*80)
    print("检查 InfluxDB 中的数据")
    print("="*80)
    
    # 配置信息（从后端 config.yaml 中读取）
    url = "http://localhost:8086"
    token = "nF4q51qJz92r4j4Z9iD5E9rK4h3m8T5d6l8O9p0Q2s3L4t5U6v7W8x9Y0z1A2b3C4d5E6f7G8h9I0j1K2L=="
    org = "ml307"
    bucket = "ml307_bucket"
    
    try:
        client = InfluxDBClient(url=url, token=token, org=org)
        
        # 查询最近 1 小时的数据
        query_api = client.query_api()
        
        query = f'''
        from(bucket: "{bucket}")
        |> range(start: -1h)
        |> filter(fn: (r) => r._measurement == "DataItem" and r.dev_serial == "078AA6C46691")
        |> sort(columns: ["_time"], desc: true)
        |> limit(n: 50)
        '''
        
        print(f"\n查询设备 078AA6C46691 最近 1 小时的数据...")
        
        tables = query_api.query(query, org=org)
        
        if not tables:
            print("  (没有数据！)")
        else:
            print(f"\n找到 {len(tables)} 个表:")
            
            for table in tables:
                print(f"\n  表:")
                for record in table.records:
                    print(f"    时间: {record.get_time()}")
                    print(f"      测量: {record.get_measurement()}")
                    print(f"      字段: {record.get_field()}")
                    print(f"      值: {record.get_value()}")
                    print(f"      标签:")
                    for k, v in record.values.items():
                        if not k.startswith('_'):
                            print(f"        {k}: {v}")
                    print()
        
        # 按 (slave, type, addr) 分组查询最新数据
        print("\n" + "="*80)
        print("查询每个地址的最新数据:")
        print("="*80)
        
        for slave in [1]:
            for mtype in [1, 4]:
                query = f'''
                from(bucket: "{bucket}")
                |> range(start: -1h)
                |> filter(fn: (r) => r._measurement == "DataItem" 
                    and r.dev_serial == "078AA6C46691"
                    and r.slave_addr == "{slave}"
                    and r.modbus_type == "{mtype}")
                |> last()
                '''
                
                tables = query_api.query(query, org=org)
                if tables:
                    print(f"\n从站 {slave} 类型 {mtype}:")
                    for table in tables:
                        for record in table.records:
                            print(f"  地址 {record.values.get('data_addr', '?')}: "
                                  f"{record.get_field()} = {record.get_value()}")
        
        client.close()
        print("\n✅ 查询完成")
        
    except Exception as e:
        print(f"\n❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_influx()
