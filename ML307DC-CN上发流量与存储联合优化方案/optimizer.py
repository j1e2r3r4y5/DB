from typing import List, Tuple, Dict


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
    阶段三~五：完整优化流程

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
