#!/usr/bin/env python3
"""
解析每个变量的实际数据
"""

def load_address_segments():
    """加载地址段配置"""
    segments = []
    with open('address_segments_final.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 4:
                segments.append({
                    'id': int(parts[0]),
                    'region': int(parts[1]),
                    'start_addr': int(parts[2]),
                    'length': int(parts[3]),
                    'name': parts[4] if len(parts) > 4 else f'seg{parts[0]}',
                    'data_type': parts[5] if len(parts) > 5 else 'uint16',
                    'init_value': parts[6] if len(parts) > 6 else None
                })
    return segments

def parse_variable_data(segments, payload_hex):
    """解析每个变量的数据"""
    
    print("=" * 80)
    print("解析每个变量的实际数据")
    print("=" * 80)
    
    payload = bytes.fromhex(payload_hex)
    offset = 0
    
    # 跳过功能码和组数
    func_code = payload[offset]
    offset += 1
    group_count = int.from_bytes(payload[offset:offset+2], 'big')
    offset += 2
    
    print(f"\n功能码: 0x{func_code:02X} (数据上传)")
    print(f"组数: {group_count}")
    
    # 按区域分组
    segments_by_region = {}
    for seg in segments:
        if seg['region'] not in segments_by_region:
            segments_by_region[seg['region']] = []
        segments_by_region[seg['region']].append(seg)
    
    # 解析每组数据
    region_data = {}
    for i in range(group_count):
        # 读取组头
        slave_id = payload[offset]
        offset += 1
        data_type = payload[offset]
        offset += 1
        start_addr = int.from_bytes(payload[offset:offset+2], 'big')
        offset += 2
        data_len = int.from_bytes(payload[offset:offset+2], 'big')
        offset += 2
        
        # 读取数据
        data = payload[offset:offset+data_len]
        offset += data_len
        
        # 数据类型 -> 区域 转换
        type_to_region = {0x00: 0, 0x01: 1, 0x03: 3, 0x04: 4}
        region = type_to_region.get(data_type, data_type)
        
        region_names = {0: "线圈(0区)", 1: "离散输入(1区)", 3: "输入寄存器(3区)", 4: "保持寄存器(4区)"}
        print(f"\n--- 组 {i+1}: {region_names.get(region, '未知')} ---")
        print(f"    起始地址: {start_addr}")
        print(f"    数据长度: {data_len} 字节")
        print(f"    原始数据: {data.hex()}")
        
        region_data[region] = {
            'start_addr': start_addr,
            'data': data
        }
    
    # 解析每个变量
    print("\n" + "=" * 80)
    print("各变量详细数据")
    print("=" * 80)
    
    for seg in segments:
        seg_id = seg['id']
        region = seg['region']
        start_addr = seg['start_addr']
        length = seg['length']
        data_type = seg['data_type']
        name = seg['name']
        
        region_names = {0: "线圈", 1: "离散输入", 3: "输入寄存器", 4: "保持寄存器"}
        
        print(f"\n📦 变量 {seg_id}: {name}")
        print(f"   区域: {region_names.get(region, '未知')}(区{region})")
        print(f"   地址: {start_addr}")
        print(f"   长度: {length} {'位' if region in [0,1] else '寄存器'}")
        print(f"   类型: {data_type}")
        
        if region not in region_data:
            print(f"   ⚠️  未在此数据包中上传")
            continue
        
        reg_data = region_data[region]
        data = reg_data['data']
        reg_start = reg_data['start_addr']
        
        # 计算变量数据的起始偏移
        if region in [0, 1]:
            # 线圈/离散输入 - 按位
            bit_start = start_addr - reg_start
            bit_end = bit_start + length
            
            byte_start = bit_start // 8
            byte_end = (bit_end + 7) // 8
            
            if byte_start >= len(data) or byte_end > len(data):
                print(f"   ⚠️  数据超出范围")
                continue
            
            # 提取位
            bits = []
            for bit_pos in range(bit_start, bit_end):
                byte_idx = bit_pos // 8
                bit_idx = bit_pos % 8
                if byte_idx < len(data):
                    bit_val = (data[byte_idx] >> bit_idx) & 0x01
                    bits.append(str(bit_val))
            
            print(f"   值: {', '.join(bits)}")
            
            if data_type == 'bool':
                bool_val = any(b == '1' for b in bits)
                print(f"   布尔值: {bool_val}")
        
        else:
            # 寄存器 - 按字
            reg_start_var = start_addr - reg_start
            reg_end_var = reg_start_var + length
            
            byte_start = reg_start_var * 2
            byte_end = reg_end_var * 2
            
            if byte_start >= len(data) or byte_end > len(data):
                print(f"   ⚠️  数据超出范围")
                continue
            
            var_data = data[byte_start:byte_end]
            print(f"   原始数据: {var_data.hex()}")
            
            if data_type == 'string':
                try:
                    text = var_data.rstrip(b'\x00').decode('utf-8', errors='ignore')
                    print(f"   字符串: '{text}'")
                except:
                    pass
            elif data_type in ['int16', 'uint16']:
                for j in range(0, len(var_data), 2):
                    if j+1 < len(var_data):
                        val = int.from_bytes(var_data[j:j+2], 'big')
                        print(f"   R{reg_start_var + j//2}: {val} (0x{val:04X})")
            elif data_type in ['int32', 'uint32', 'float32']:
                if len(var_data) >= 4:
                    if data_type == 'float32':
                        import struct
                        val = struct.unpack('>f', var_data[:4])[0]
                        print(f"   值: {val}")
                    else:
                        val = int.from_bytes(var_data[:4], 'big')
                        print(f"   值: {val} (0x{val:08X})")

def main():
    segments = load_address_segments()
    
    # 实际数据包
    payload_hex = "0500040100000000040101010101010000000501010100010103000000284142434445464748494a4b4c4d000000000000000000000000004142434445464748494a4b4c4d000104000000284142434445464748494a4b4c4d000000000000000000000000004142434445464748494a4b4c4d00"
    
    parse_variable_data(segments, payload_hex)

if __name__ == "__main__":
    main()

