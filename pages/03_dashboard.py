import streamlit as st
import pandas as pd
import json
import os
from style_manager import apply_pro_style

# 1. 基础配置
st.set_page_config(layout="wide", page_title="Warehouse Control")
apply_pro_style()

# 路径定义
JSON_DB = "data/creative_db.json"
TXT_FILES = {
    "Subject": "data/subjects.txt",
    "Action": "data/actions.txt",
    "Style": "data/styles.txt",
    "Mood": "data/moods.txt",
    "Usage": "data/usage.txt"
}

# 2. 核心数据加载大脑
def load_db():
    # 如果文件不存在，直接初始化基础结构
    if not os.path.exists(JSON_DB):
        init_data = {cat: [] for cat in TXT_FILES.keys()}
        with open(JSON_DB, 'w', encoding='utf-8') as f:
            json.dump(init_data, f, indent=4, ensure_ascii=False)
        return init_data
    
    with open(JSON_DB, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return {cat: [] for cat in TXT_FILES.keys()}

def save_db(data):
    with open(JSON_DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# 3. 初始化数据
db = load_db()

st.title("🎮 仓库权重中控台")

# --- 💡 特别整活：一键搬家工具 ---
with st.expander("🛠️ 首次使用？点击将 TXT 导入 JSON"):
    st.info("检测到新地基，点击下方按钮将旧的 .txt 词汇同步到此管理台。")
    if st.button("🚀 开始一键搬家 (TXT -> JSON)"):
        count = 0
        for cat, path in TXT_FILES.items():
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    words = [line.strip() for line in f.readlines() if line.strip()]
                    for w in words:
                        # 检查是否重复
                        if w not in [x['val'] for x in db[cat]]:
                            db[cat].append({
                                "val": w,
                                "tags": {"target": "all", "vibe": "general"},
                                "weight_bonus": 1.0
                            })
                            count += 1
        save_db(db)
        st.success(f"搬家完成！共迁移 {count} 个词汇。请刷新页面查看。")
        st.rerun()

# --- 4. 可视化编辑逻辑 ---
# 将 JSON 扁平化为表格
rows = []
for cat, items in db.items():
    for item in items:
        rows.append({
            "分类": cat,
            "关键词": item.get('val', ''),
            "人群(target)": item.get('tags', {}).get('target', 'all'),
            "调性(vibe)": item.get('tags', {}).get('vibe', 'general'),
            "手动加权": item.get('weight_bonus', 1.0)
        })

if rows:
    df = pd.DataFrame(rows)
    st.subheader("📋 标签与权重明细 (修改后记得点保存)")
    
    # 使用表格编辑器
    edited_df = st.data_editor(
        df, 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "手动加权": st.column_config.NumberColumn(min_value=0.1, max_value=10.0, step=0.1)
        }
    )

    # 保存修改
    if st.button("💾 同步修改到全局数据库", type="primary"):
        # 将表格数据还原为 JSON 结构
        new_db = {cat: [] for cat in TXT_FILES.keys()}
        for _, row in edited_df.iterrows():
            cat = row['分类']
            if cat in new_db:
                new_db[cat].append({
                    "val": row['关键词'],
                    "tags": {
                        "target": row['人群(target)'],
                        "vibe": row['调性(vibe)']
                    },
                    "weight_bonus": row['手动加权']
                })
        save_db(new_db)
        st.success("🎉 数据同步成功！创意引擎已更新。")
else:
    st.warning("📭 仓库目前是空的，请先使用上方的“搬家工具”或手动添加数据。")

# 5. 状态统计
st.divider()
cols = st.columns(len(db.keys()))
for i, (cat, items) in enumerate(db.items()):
    cols[i].metric(cat, len(items))
