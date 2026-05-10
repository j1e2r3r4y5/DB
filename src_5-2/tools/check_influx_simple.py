#!/usr/bin/env python3
"""
简单检查 InfluxDB 中的数据
"""
import requests
import json

def check_influx():
    print("="*80)
    print("检查 InfluxDB 中的数据")
    print("="*80)
    
    # InfluxDB v1 API 查询（更简单）
    query = 'SELECT * FROM "DataItem" WHERE "dev_serial" = \'078AA6C46691\' ORDER BY time DESC LIMIT 20'
    
    try:
        # 尝试用 InfluxDB v1 API 查询
        response = requests.get(
            'http://localhost:8086/query',
            params={
                'db': 'ml307_bucket',
                'q': query
            },
            timeout=5
        )
        
        print(f"\n查询状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n查询结果: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if 'results' in data and len(data['results']) > 0:
                result = data['results'][0]
                if 'series' in result and len(result['series']) > 0:
                    series = result['series'][0]
                    print(f"\n找到数据点: {len(series['values'])} 个")
                    
                    # 打印前5个点
                    cols = series['columns']
                    for i, row in enumerate(series['values'][:5]):
                        print(f"\n数据点 {i+1}:")
                        for col, val in zip(cols, row):
                            print(f"  {col}: {val}")
            else:
                print("\n没有找到数据！")
        else:
            print(f"\n查询失败: {response.text}")
            
    except Exception as e:
        print(f"\n❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n\n尝试 v2 API...")
        # 如果 v1 不行，尝试用 v2 API 简单查询
        try:
            # 简单的健康检查
            response = requests.get('http://localhost:8086/health', timeout=3)
            print(f"InfluxDB 健康检查: {response.status_code}")
        except Exception as e2:
            print(f"InfluxDB 连接失败: {e2}")

if __name__ == "__main__":
    check_influx()
