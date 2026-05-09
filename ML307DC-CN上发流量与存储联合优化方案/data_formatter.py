from typing import List, Tuple


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
