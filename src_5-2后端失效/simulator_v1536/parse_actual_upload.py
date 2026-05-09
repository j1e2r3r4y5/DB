#!/usr/bin/env python3
"""
解析实际的数据上传数据包
"""

def parse_05_payload(payload_hex):
    """解析 0x05 数据包"""
    
    print("=" * 80)
    print("解析实际 0x05 数据上传数据包")
    print("=" * 80)
    
    print(f"\n原始数据包: {payload_hex}")
    print(f"总长度: {len(payload_hex) // 2} 字节")
    
    offset = 0
    payload = bytes.fromhex(payload_hex)
    
    # 功能码
    func_code = payload[offset]
    offset += 1
    print(f"\n[{offset-1:2d}] 0x{func_code:02X} - 功能码 (0x05 = 数据上传)")
    
    # 组数
    group_count = int.from_bytes(payload[offset:offset+2], 'big')
    offset += 2
    print(f"[{offset-2:2d}] 0x{group_count:04X} - 组数 ({group_count})")
    
    # 解析每组数据
    for i in range(group_count):
        print(f"\n--- 组 {i+1} ---")
        
        # 从站ID
        slave_id = payload[offset]
        offset += 1
        print(f"[{offset-1:2d}] 0x{slave_id:02X} - 从站ID")
        
        # 数据类型
        data_type = payload[offset]
        offset += 1
        type_names = {0x00: "线圈(0区)", 0x01: "离散输入(1区)", 0x03: "输入寄存器(3区)", 0x04: "保持寄存器(4区)"}
        print(f"[{offset-1:2d}] 0x{data_type:02X} - 数据类型 ({type_names.get(data_type, '未知')})")
        
        # 起始地址
        start_addr = int.from_bytes(payload[offset:offset+2], 'big')
        offset += 2
        print(f"[{offset-2:2d}] 0x{start_addr:04X} - 起始地址 ({start_addr})")
        
        # 数据长度
        data_len = int.from_bytes(payload[offset:offset+2], 'big')
        offset += 2
        print(f"[{offset-2:2d}] 0x{data_len:04X} - 数据长度 ({data_len} 字节)")
        
        # 数据内容
        data = payload[offset:offset+data_len]
        offset += data_len
        
        print(f"[{offset-data_len:2d}] {data.hex()} - 数据")
        
        # 解析数据内容
        if data_type in [0x00, 0x01]:
            # 线圈/离散输入 - 按位解析
            bits = []
            for byte_idx, byte in enumerate(data):
                for bit_idx in range(8):
                    bit_pos = byte_idx * 8 + bit_idx
                    bit_val = (byte >> bit_idx) & 0x01
                    bits.append(f"{bit_pos}={bit_val}")
            print(f"      位解析: {', '.join(bits[:16])}{'...' if len(bits) > 16 else ''}")
        else:
            # 寄存器 - 尝试解析字符串
            try:
                text = data.rstrip(b'\x00').decode('utf-8', errors='ignore')
                if text:
                    print(f"      字符串: '{text}'")
            except:
                pass
            
            # 显示寄存器值
            regs = []
            for j in range(0, data_len, 2):
                if j+1 < data_len:
                    reg_val = int.from_bytes(data[j:j+2], 'big')
                    regs.append(f"R{j//2}=0x{reg_val:04X}")
            print(f"      寄存器: {', '.join(regs[:8])}{'...' if len(regs) > 8 else ''}")
    
    print(f"\n[{offset:2d}] - 结束 (总计 {offset} 字节)")
    print("\n" + "=" * 80)

def main():
    # 实际数据包
    payload_hex = "0500040100000000040101010101010000000501010100010103000000284142434445464748494a4b4c4d000000000000000000000000004142434445464748494a4b4c4d000104000000284142434445464748494a4b4c4d000000000000000000000000004142434445464748494a4b4c4d00"
    
    parse_05_payload(payload_hex)

if __name__ == "__main__":
    main()

