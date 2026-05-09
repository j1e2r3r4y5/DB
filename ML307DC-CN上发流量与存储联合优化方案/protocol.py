from typing import List, Tuple


def compute_original_payload(original: List[Tuple[int, int, int]]) -> int:
    """
    计算原始方案（简单合并）的payload
    用于对比优化效果
    """
    # 简单合并：每个分区取 min 到 max
    zone1_min = None
    zone1_max = None
    zone4_min = None
    zone4_max = None

    for partition, address, length in original:
        if partition == 1:
            if zone1_min is None or address < zone1_min:
                zone1_min = address
            if zone1_max is None or (address + length - 1) > zone1_max:
                zone1_max = address + length - 1
        elif partition == 4:
            if zone4_min is None or address < zone4_min:
                zone4_min = address
            if zone4_max is None or (address + length - 1) > zone4_max:
                zone4_max = address + length - 1

    K = 0
    B1 = 0
    R4 = 0

    if zone1_min is not None:
        K += 1
        start_byte = zone1_min // 8
        end_byte = zone1_max // 8
        B1 = end_byte - start_byte + 1

    if zone4_min is not None:
        K += 1
        R4 = zone4_max - zone4_min + 1

    payload = 3 + 6 * K + B1 + 2 * R4
    return payload


def encode_04_payload(opt_segments: List[Tuple[int, int, int]]) -> str:
    """
    生成04下发报文（十六进制大写）

    Returns:
        hex_str: 十六进制字符串
    """
    buffer = []
    buffer.append(0x04)  # 功能码

    K = len(opt_segments)
    buffer.append((K >> 8) & 0xFF)
    buffer.append(K & 0xFF)

    for zone, start, length in opt_segments:
        buffer.append(0x01)  # 从站地址固定01
        buffer.append(0x01 if zone == 1 else 0x04)  # 类型字节
        buffer.append((start >> 8) & 0xFF)
        buffer.append(start & 0xFF)
        buffer.append((length >> 8) & 0xFF)
        buffer.append(length & 0xFF)

    hex_str = ''.join(f'{b:02X}' for b in buffer)
    return hex_str


def write_optimized_txt(
    opt_segments: List[Tuple[int, int, int]],
    seed: str,
    output_dir: str = "."
) -> str:
    """
    生成优化后TXT文件

    Returns:
        txt_path: 输出文件路径
    """
    txt_path = f"{output_dir}/{seed}_optimized.txt"
    with open(txt_path, "w", encoding="utf-8", newline="\n") as f:
        for idx, (zone, start, length) in enumerate(opt_segments, start=1):
            f.write(f"{zone} {start} {length} {idx}\n")
    return txt_path
