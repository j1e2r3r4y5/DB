import random
from typing import List, Tuple

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
) -> str:
    """
    阶段二：优化前展开与输出文件

    生成 {seed}.txt
    """
    original: List[Tuple[int, int, int, int]] = []

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

    return filepath


if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) < 2:
        print("Usage: python generate_test_data.py <seed> [output_dir]")
        sys.exit(1)

    seed = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."

    intervals_1, intervals_4 = generate_raw_segments(seed)
    print(f"Generated: zone1={len(intervals_1)} segments, zone4={len(intervals_4)} segments")

    filepath = expand_and_write_output(intervals_1, intervals_4, seed, output_dir)
    print(f"Output: {filepath}")
