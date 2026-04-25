#!/usr/bin/env python3
"""
使用md2html_tool转换src_5-0的文档
"""
import sys
import os

# 添加src_5项目中的md2html_tool到路径
md2html_path = os.path.join(os.path.dirname(__file__), '..', 'src_5', 'md2html_tool')
sys.path.insert(0, md2html_path)

try:
    from src import MarkdownToHTML, PRESETS
except ImportError as e:
    print(f"导入失败: {e}")
    print("请确保src_5项目在同级目录下")
    sys.exit(1)


def main():
    print("=" * 60)
    print("转换 Modbus寄存器区间划分算法设计文档")
    print("=" * 60)
    
    # 配置：使用full预设
    config = PRESETS['full']
    
    generator = MarkdownToHTML(config=config)
    
    # Markdown文件路径
    current_dir = os.path.dirname(__file__)
    md_file = os.path.join(current_dir, 'docs', 'Modbus寄存器区间划分算法设计文档.md')
    
    if not os.path.exists(md_file):
        print(f"❌ 文件不存在: {md_file}")
        return
    
    try:
        print(f"正在处理: {md_file}")
        
        # 创建html输出目录
        html_dir = os.path.join(current_dir, 'html')
        if not os.path.exists(html_dir):
            os.makedirs(html_dir, exist_ok=True)
        
        # 输出文件路径
        output_file = os.path.join(html_dir, 'Modbus寄存器区间划分算法设计文档.html')
        
        generator.convert_file(md_file, output_file)
        print(f"✅ 成功生成: {output_file}")
        
        print("\n" + "=" * 60)
        print("完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

