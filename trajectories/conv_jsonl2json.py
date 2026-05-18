#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

def jsonl_to_json(input_path: str):
    # 自动生成同名json路径
    input_file = Path(input_path)
    output_file = input_file.with_suffix('.json')
    
    json_data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            json_data.append(item)

    # 写入格式化JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)

    print(f"✅ 转换完成")
    print(f"输入: {input_path}")
    print(f"输出: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法：python jsonl2json.py 输入文件.jsonl")
        print("示例：python jsonl2json.py data.jsonl")
        sys.exit(1)
    
    jsonl_to_json(sys.argv[1])