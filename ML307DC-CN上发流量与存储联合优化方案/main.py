#!/usr/bin/env python3
"""
ML307DC-CN 流量与存储联合优化工具

主要功能：
1. 生成随机地址段（阶段一~二）
2. 优化已有地址段配置（阶段三~五）

使用方式：
    # 生成模式：根据seed生成新数据
    python main.py <seed> [output_dir]

    # 优化模式：读取现有文件进行优化
    python main.py --optimize <file> [output_dir]
"""

import sys
import os

from segment_generator import generate_raw_segments
from data_formatter import expand_and_write_output, parse_original_from_file
from optimizer import optimize_segments, extract_must_cover
from protocol import compute_original_payload, encode_04_payload, write_optimized_txt


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    if sys.argv[1] == "--optimize":
        # 优化模式：读取现有文件进行优化
        if len(sys.argv) < 3:
            print_usage()
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
    opt_txt_path = write_optimized_txt(opt_segments, seed, output_dir)
    hex_str = encode_04_payload(opt_segments)
    print(f"\n[输出]")
    print(f"  优化后TXT: {opt_txt_path}")
    print(f"  04下发报文: {hex_str}")


def print_usage():
    print("Usage:")
    print("  python main.py <seed> [output_dir]          # 生成模式")
    print("  python main.py --optimize <file> [output_dir]  # 优化模式")


if __name__ == "__main__":
    main()
