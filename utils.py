import json
import requests

def load_json(file_path):
    """加载JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_jsonl(file_path):
    """加载JSONL文件（每行一个独立JSON对象）"""
    jsonl_data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped_line = line.strip()
            if not stripped_line:
                continue
            jsonl_data.append(json.loads(stripped_line))
    return jsonl_data

def save_json(data, file_path):
    """保存JSON文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def sync_exec_sql(sql: str, db_id: str):
    """同步调用本地 Flask 服务进行 SQL 执行"""
    payload = {
        "db_id": db_id,
        "sql": sql,
        "timeout": 60
    }
    try:
        response = requests.post(
            url="http://127.0.0.1:11111/execute_sql",
            json=payload,
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('status'), data.get('result')
        return 0, "请求失败"
    except Exception as e:
        print(f"Eval API Error for {db_id}: {e}")
        return 0, "API失效"

def sync_compare_sql(pred_sql: str, gold_sql:str, db_id: str):
    """同步调用本地 Flask 服务进行 SQL 执行"""
    payload = {
            "db_id": db_id,
            "predicted_sql": pred_sql,
            "ground_truth": gold_sql,
            "timeout": 60
        }

    try:
        response = requests.post(
            url="http://127.0.0.1:11111/compare_sql",
            json=payload,
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('status'), data.get('result')
        return 0, "请求失败"
    except Exception as e:
        print(f"Eval API Error for {db_id}: {e}")
        return 0, "API失效"


def exec_sql(sql: str, db_id: str):
    # 调用你原来的函数
    status, result = sync_exec_sql(sql, db_id)
    result = str(result)
    if len(result) > 500:
        result = result[:500] + '... (Omitted for brevity)'
    # 格式化返回给 AI（让AI看得懂）
    if status == 1:
        return f"✅ SQL执行成功，结果：{result}"
    else:
        return f"❌ SQL执行失败，原因：{result}"
