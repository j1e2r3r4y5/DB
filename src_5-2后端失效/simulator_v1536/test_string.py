
#!/usr/bin/env python3
"""
测试字符串填入寄存器 -> 读取 -> 解码的完整流程
找出为什么只显示 "ML" 的问题
"""
import struct


def test_string_flow():
    """模拟整个字符串处理流程"""
    print("=== 测试流程开始 ===\n")

    device_desc = "ML307-Smart-Meter-001"
    print(f"原始字符串: {device_desc}\n")

    desc_bytes = device_desc.encode('utf-8')[:20]
    print(f"原始字节串 (UTF-8): {desc_bytes.hex()} (len={len(desc_bytes)})\n")

    registers = []
    print("--- 填入寄存器过程 ---")
    for i in range(10):
        byte_offset = i * 2
        reg_value = 0
        if byte_offset < len(desc_bytes):
            reg_value = (desc_bytes[byte_offset] << 8)
            print(f"  寄存器 {i}: 高字节 = 0x{desc_bytes[byte_offset]:02X} (字符: '{chr(desc_bytes[byte_offset])}')")
        if byte_offset + 1 < len(desc_bytes):
            reg_value |= desc_bytes[byte_offset + 1]
            print(f"  寄存器 {i}: 低字节 = 0x{desc_bytes[byte_offset + 1]:02X} (字符: '{chr(desc_bytes[byte_offset + 1])}')")
        registers.append(reg_value)
        print(f"  寄存器 {i} 值 = 0x{reg_value:04X}\n")

    print("--- Modbus read_holding_registers 输出字节流 ---")
    data_out = bytearray()
    for val in registers:
        data_out.extend(struct.pack('>H', val & 0xFFFF))

    print(f"Modbus 输出字节流: {data_out.hex()} (len={len(data_out)})\n")

    print("--- 后端解码（假设直接 string(data_out[:20])） ---")
    decoded_str = bytes(data_out[:20]).decode('utf-8', errors='replace')
    print(f"直接解码结果: '{decoded_str}'")
    print(f"长度: {len(decoded_str)}\n")

    print("=== 结论 ===")
    print("如果上面的直接解码结果只显示 'ML'，说明问题就在这里！")


if __name__ == "__main__":
    test_string_flow()
