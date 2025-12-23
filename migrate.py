import json
import os

# 1. 定义你的老仓库路径
TXT_FILES = {
    "Subject": "data/subjects.txt",
    "Action": "data/actions.txt",
    "Style": "data/styles.txt",
    "Mood": "data/moods.txt",
    "Usage": "data/usage.txt"
}

# 2. 定义新地基路径
JSON_DB = "data/creative_db.json"

def migrate():
    new_db = {}
    
    for category, path in TXT_FILES.items():
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                # 读取txt里的每一行，去掉空格
                words = [line.strip() for line in f.readlines() if line.strip()]
                
                # 将每个词包装成“结构化数据”
                # 默认给它们打上基础标签，方便你之后在 Dashboard 修改
                new_db[category] = [
                    {
                        "val": w, 
                        "tags": {"target": "all", "vibe": "general"}, 
                        "weight_bonus": 1.0
                    } for w in words
                ]
            print(f"✅ 已转换 {category}: {len(words)} 个词")

    # 3. 写入 JSON 文件
    with open(JSON_DB, 'w', encoding='utf-8') as f:
        json.dump(new_db, f, indent=4, ensure_ascii=False)
    print(f"\n🚀 搬家完成！新地基已生成在: {JSON_DB}")

if __name__ == "__main__":
    migrate()
