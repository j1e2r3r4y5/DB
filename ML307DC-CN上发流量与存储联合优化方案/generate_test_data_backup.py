import random
from typing import List, Tuple, Dict

MAX_BITS = 1536
MAX_REGS = 12288
ADDRESS_SPACE_END = 65535


def generate_raw_segments(seed: str) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    """
    阶段一：原始地址段生成

    Returns:
        intervals_1: List of (start, end) for zone 1 (bits)
        intervals_4: List of (start, end) for zone 4 (registers)
    """
    random.seed(seed)
    S = random.randint(1, 30)

    intervals_1: List[Tuple[int, int]] = []
    intervals_4: List[Tuple[int, int]] = []
    used_bits_1 = 0
    used_regs_4 = 0

    for _ in range(S):
        can_1 = used_bits_1 < MAX_BITS
        can_4 = used_regs_4 < MAX_REGS

        if not can_1 and not can_4:
            break

        if can_1 and can_4:
            zone = random.choice([1, 4])
        elif can_1:
            zone = 1
        else:
            zone = 4

        if zone == 1:
            free_intervals = compute_free_intervals(intervals_1)
            if not free_intervals:
                continue

            f_start, f_end = random.choice(free_intervals)
            max_len = min(f_end - f_start + 1, MAX_BITS - used_bits_1)
            if max_len < 1:
                continue

            length = random.randint(1, max_len)
            start = random.randint(f_start, f_end - length + 1)
            intervals_1.append((start, start + length - 1))
            used_bits_1 += length

        else:
            free_intervals = compute_free_intervals(intervals_4)
            if not free_intervals:
                continue

            f_start, f_end = random.choice(free_intervals)
            max_len = min(f_end - f_start + 1, MAX_REGS - used_regs_4)
            if max_len < 1:
                continue

            length = random.randint(1, max_len)
            start = random.randint(f_start, f_end - length + 1)
            intervals_4.append((start, start + length - 1))
            used_regs_4 += length

    assert used_bits_1 <= MAX_BITS, f"违反硬约束（1区合计>{MAX_BITS}）"
    assert used_regs_4 <= MAX_REGS, f"违反硬约束（4区合计>{MAX_REGS}）"

    return intervals_1, intervals_4


def compute_free_intervals(
    existing: List[Tuple[int, int]]
) -> List[Tuple[int, int]]:
    """
    计算当前空闲区间列表
    输入: [(s1,e1), (s2,e2), ...] 已排序无重叠
    输出: [[f1_start, f1_end], [f2_start, f2_end], ...]
    """
    if not existing:
        return [(0, ADDRESS_SPACE_END)]

    existing = sorted(existing)
    free = []

    if existing[0][0] > 0:
        free.append((0, existing[0][0] - 1))

    for i in range(len(existing) - 1):
        if existing[i][1] + 1 <= existing[i + 1][0] - 1:
            free.append((existing[i][1] + 1, existing[i + 1][0] - 1))

    if existing[-1][1] < ADDRESS_SPACE_END:
        free.append((existing[-1][1] + 1, ADDRESS_SPACE_END))

    return free


def expand_and_write_output(
    intervals_1: List[Tuple[int, int]],
    intervals_4: List[Tuple[int, int]],
    seed: str,
    output_dir: str = "."
) -> Tuple[str, List[Tuple[int, int, int]]]:
    """
    阶段二：优化前展开与输出文件

    生成 {seed}.txt
    """
    original: List[Tuple[int, int, int]] = []

    for s, e in intervals_1:
        for bit in range(s, e + 1):
            original.append((1, bit, 1))

    for s, e in intervals_4:
        original.append((4, s, e - s + 1))

    original.sort(key=lambda x: (x[0], x[1]))

    filepath = f"{output_dir}/{seed}.txt"
    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        for idx, (partition, address, length) in enumerate(original, start=1):
            f.write(f"{idx} {partition} {address} {length}\n")

    return filepath, original


def parse_original_from_file(filepath: str) -> List[Tuple[int, int, int]]:
    """
    从文件解析原始数据
    """
    original = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            idx, partition, address, length = map(int, parts[:4])
            original.append((partition, address, length))
    return original


def extract_must_cover(original: List[Tuple[int, int, int]]) -> Tuple[List[int], List[int]]:
    """
    阶段三：提取优化必须覆盖的集合

    Returns:
        must_bytes_1: 排序后的字节索引列表
        must_regs_4: 排序后的寄存器索引列表
    """
    # 1区必须覆盖的字节集合
    byte_set_1 = set()
    for partition, address, length in original:
        if partition == 1:
            byte_idx = address // 8
            byte_set_1.add(byte_idx)
    must_bytes_1 = sorted(byte_set_1)

    # 4区必须覆盖的寄存器集合
    reg_set_4 = set()
    for partition, address, length in original:
        if partition == 4:
            for reg in range(address, address + length):
                reg_set_4.add(reg)
    must_regs_4 = sorted(reg_set_4)

    return must_bytes_1, must_regs_4


def compute_options(points: List[int], max_len: int) -> Dict[int, int]:
    """
    阶段四：单区最优覆盖函数

    Args:
        points: 已排序、无重复的必须点列表
        max_len: 最大允许长度

    Returns:
        {段数: 总长度}
    """
    if not points:
        return {0: 0}

    # 计算相邻点间隙
    gaps = []
    for i in range(len(points) - 1):
        gap = points[i + 1] - points[i] - 1
        gaps.append((gap, i))

    # 按间隙升序排列
    gaps.sort()

    # 前缀和
    prefix = [0]
    current = 0
    for gap, _ in gaps:
        current += gap
        prefix.append(current)

    # 对 K 从 1 开始
    options = {}
    n = len(points)
    max_k = min(n, 30)
    for K in range(1, max_k + 1):
        if K >= n:
            total_len = n
        else:
            r = n - K
            total_len = n + prefix[r]
        if total_len <= max_len:
            options[K] = total_len

    return options


def build_intervals(points: List[int], K: int) -> List[Tuple[int, int]]:
    """
    阶段五：分段函数

    Returns:
        [(start, end), ...]
    """
    if not points:
        return []

    if K >= len(points):
        return [(p, p) for p in points]

    # 计算间隙（带索引）
    gaps = []
    for i in range(len(points) - 1):
        gap = points[i + 1] - points[i] - 1
        gaps.append((gap, i))

    # 按间隙降序排序
    gaps.sort(reverse=True, key=lambda x: x[0])

    # 取前 K-1 个间隙作为分割点
    split_indices = sorted([gap[1] for gap in gaps[:K - 1]])

    # 构建块
    blocks = []
    prev = 0
    for idx in split_indices:
        blocks.append((points[prev], points[idx]))
        prev = idx + 1
    blocks.append((points[prev], points[-1]))

    return blocks


def optimize_segments(original: List[Tuple[int, int, int]]) -> Tuple[Dict, List[Tuple[int, int, int]], int]:
    """
    阶段四~五：完整优化流程

    Returns:
        best_sol: {K1, B1, K4, R4, payload, total_addr}
        opt_segments: [(zone, start, length), ...]
        payload: 优化后的payload长度
    """
    # 阶段三
    must_bytes_1, must_regs_4 = extract_must_cover(original)

    # 阶段四
    opt1 = compute_options(must_bytes_1, 192)  # 192字节 = 1536位
    opt4 = compute_options(must_regs_4, 12288)

    # 可行性检查
    if must_bytes_1 and not opt1:
        raise Exception("无法满足优化硬约束（1区）")
    if must_regs_4 and not opt4:
        raise Exception("无法满足优化硬约束（4区）")

    # 组合枚举找最优
    K1_candidates = [0] if not must_bytes_1 else list(opt1.keys())
    K4_candidates = [0] if not must_regs_4 else list(opt4.keys())

    best_payload = float('inf')
    best_total_addr = float('inf')
    best_sol = None

    for K1 in K1_candidates:
        for K4 in K4_candidates:
            K_total = K1 + K4
            if K_total > 30:
                continue

            B1 = opt1.get(K1, 0)
            R4 = opt4.get(K4, 0)

            payload = 3 + 6 * K_total + B1 + 2 * R4
            total_addr = 8 * B1 + R4

            if (payload < best_payload) or \
               (payload == best_payload and total_addr < best_total_addr):
                best_payload = payload
                best_total_addr = total_addr
                best_sol = {
                    'K1': K1, 'B1': B1,
                    'K4': K4, 'R4': R4,
                    'payload': payload,
                    'total_addr': total_addr
                }

    if not best_sol:
        raise Exception("无法满足优化硬约束")

    # 阶段五：重构优化段
    byte_blocks = build_intervals(must_bytes_1, best_sol['K1'])
    reg_blocks = build_intervals(must_regs_4, best_sol['K4'])

    # 转换为最终优化段
    opt_segments = []
    for b_start, b_end in byte_blocks:
        zone = 1
        start = b_start * 8
        length = (b_end - b_start + 1) * 8
        opt_segments.append((zone, start, length))

    for r_start, r_end in reg_blocks:
        zone = 4
        start = r_start
        length = r_end - r_start + 1
        opt_segments.append((zone, start, length))

    # 按 (zone, start) 排序
    opt_segments.sort(key=lambda x: (x[0], x[1]))

    return best_sol, opt_segments, best_sol['payload']


def write_optimized_output(
    opt_segments: List[Tuple[int, int, int]],
    seed: str,
    output_dir: str = "."
) -> Tuple[str, str]:
    """
    阶段五：生成优化后TXT和04下发报文

    Returns:
        (txt_path, hex_str)
    """
    # 生成优化后TXT
    txt_path = f"{output_dir}/{seed}_optimized.txt"
    with open(txt_path, "w", encoding="utf-8", newline="\n") as f:
        for idx, (zone, start, length) in enumerate(opt_segments, start=1):
            f.write(f"{zone} {start} {length} {idx}\n")

    # 生成04下发报文
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
    return txt_path, hex_str


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


if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) < 2:
        print("Usage: python generate_test_data.py <seed> [output_dir]")
        print("       python generate_test_data.py --optimize <file> [output_dir]")
        sys.exit(1)

    if sys.argv[1] == "--optimize":
        # 优化模式：读取现有文件进行优化
        if len(sys.argv) < 3:
            print("Usage: python generate_test_data.py --optimize <file> [output_dir]")
            sys.exit(1)
        input_file = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else "."
        seed = os.path.splitext(os.path.basename(input_file))[0]

        print(f"[优化模式] 读取文件: {input_file}")
        original = parse_original_from_file(input_file)
    else:
        # 生成模式：生成新数据
        seed = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "."

        print(f"[生成模式] seed={seed}")
        intervals_1, intervals_4 = generate_raw_segments(seed)
        print(f"  阶段一: 生成 {len(intervals_1)} 个1区段, {len(intervals_4)} 个4区段")
        filepath, original = expand_and_write_output(intervals_1, intervals_4, seed, output_dir)
        print(f"  阶段二: 输出 {filepath}")

    # 阶段三~五：优化
    print(f"\n[优化流程]")
    must_bytes_1, must_regs_4 = extract_must_cover(original)
    print(f"  阶段三: 1区必须字节={len(must_bytes_1)}, 4区必须寄存器={len(must_regs_4)}")

    # 计算原始payload（简单合并）
    original_payload = compute_original_payload(original)
    print(f"  原始方案payload: {original_payload} 字节")

    # 优化
    best_sol, opt_segments, payload = optimize_segments(original)
    print(f"  阶段四~五: 优化完成!")
    print(f"    K1={best_sol['K1']}, B1={best_sol['B1']}")
    print(f"    K4={best_sol['K4']}, R4={best_sol['R4']}")
    print(f"    优化后payload: {payload} 字节")
    print(f"    节省: {original_payload - payload} 字节 ({(1 - payload/original_payload)*100:.1f}%)")

    # 输出优化结果
    opt_txt_path, hex_str = write_optimized_output(opt_segments, seed, output_dir)
    print(f"\n[输出]")
    print(f"  优化后TXT: {opt_txt_path}")
    print(f"  04下发报文: {hex_str}")
