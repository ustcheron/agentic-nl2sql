import pandas as pd
import sys
import os

def convert_json_to_parquet(input_path):
    # 1. 检查文件是否存在
    if not os.path.exists(input_path):
        print(f"Error: 找不到文件 '{input_path}'")
        return

    # 2. 生成输出路径（同名但后缀为 .parquet，保存在当前目录）
    base_name = os.path.basename(input_path)
    file_name_without_ext = os.path.splitext(base_name)[0]
    output_path = f"{file_name_without_ext}.parquet"

    try:
        print(f"正在读取: {input_path} ...")
        
        # 3. 读取 JSON
        # lines=True 适用于每行一个 JSON 对象的格式（常见的日志/大数据格式）
        # 如果是标准的 JSON 数组，请去掉 lines=True
        try:
            df = pd.read_json(input_path, lines=True)
        except ValueError:
            # 如果按行读取失败，尝试按标准格式读取
            df = pd.read_json(input_path)

        # 4. 转换为 Parquet
        df.to_parquet(output_path, engine='pyarrow', index=False)
        
        print(f"转换成功！已保存至: {os.path.abspath(output_path)}")
        
    except Exception as e:
        print(f"转换过程中出错: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python json2parquet.py <json文件路径>")
    else:
        convert_json_to_parquet(sys.argv[1])
