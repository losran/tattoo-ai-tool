import streamlit as st
import json
import os
import pandas as pd

# --- 1. 配置与数据地基 ---
st.set_page_config(layout="wide", page_title="仓库权重中控台")

JSON_DB_PATH = "data/creative_db.json"
WAREHOUSE_CONFIG = {
    "Subject": "data/subjects.txt",
    "Action": "data/actions.txt",
    "Style": "data/styles.txt",
    "Mood": "data/moods.txt",
    "Usage": "data/usage.txt"
}

def load_db():
    if os.path.exists(JSON_DB_PATH):
        with open(JSON_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    # 如果没有文件，初始化一个标准结构
    return {
        "words": {cat: [] for cat in WAREHOUSE_CONFIG.keys()},
        "templates": {
            "完全随机模式": {"pref_vibe": [], "pref_target": [], "boost": 1.0}
        }
    }

def save_db(data):
    os.makedirs("data", exist_ok=True)
    with open(JSON_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

db = load_db()

# --- 2. 界面头部 ---
st.title("🎮 仓库权重中控台")

# 这里保留你的搬家工具，以防万一
with st.expander("🛠️ 首次使用？点击将旧 TXT 导入 JSON"):
    if st.button("开始一键搬家"):
        for cat, path in WAREHOUSE_CONFIG.items():
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    lines = [l.strip() for l in f if l.strip()]
                    # 搬家时赋予默认权重 1.0 和 general 标签
                    db["words"][cat] = [{"val": l, "weight_bonus": 1.0, "tags": {"vibe": "general", "target": "all"}} for l in lines]
        save_db(db)
        st.success("搬家完成！")
        st.rerun()

# --- 3. 核心调控区 (双 Tab 布局) ---
tab_words, tab_templates = st.tabs(["🏷️ 词库与权重调控", "🎯 意图模板配置"])

with tab_words:
    st.subheader("词库可视化编辑")
    category = st.selectbox("选择要调控的维度", list(WAREHOUSE_CONFIG.keys()))
    
    # 将 JSON 数据转为表格
    words_data = db["words"].get(category, [])
    if words_data:
        # 为了方便编辑，我们要把 tags 里的内容摊平
        flat_data = []
        for item in words_data:
            flat_data.append({
                "词汇": item["val"],
                "权重分数": item.get("weight_bonus", 1.0),
                "调性(vibe)": item["tags"].get("vibe", "general"),
                "人群(target)": item["tags"].get("target", "all")
            })
        
        df = pd.DataFrame(flat_data)
        
        # 💡 神器：可视化编辑器
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "权重分数": st.column_config.NumberColumn(min_value=0.1, max_value=20.0, step=0.1)
            }
        )
        
        if st.button(f"💾 保存 {category} 的修改"):
            # 还原回 JSON 格式
            new_list = []
            for _, row in edited_df.iterrows():
                new_list.append({
                    "val": row["词汇"],
                    "weight_bonus": float(row["权重分数"]),
                    "tags": {"vibe": row["调性(vibe)"], "target": row["人群(target)"]}
                })
            db["words"][category] = new_list
            save_db(db)
            st.success("保存成功！")
    else:
        st.info("该维度目前是空的。")

with tab_templates:
    st.subheader("意图模板可视化调控")
    st.caption("在这里增加模板，创意引擎页面的下拉框会自动同步。")
    
    # 转换模板数据
    tpl_rows = []
    for name, cfg in db["templates"].items():
        tpl_rows.append({
            "模板名称": name,
            "偏好调性(用逗号隔开)": ",".join(cfg["pref_vibe"]),
            "偏好人群(用逗号隔开)": ",".join(cfg["pref_target"]),
            "加权倍率(Boost)": cfg["boost"]
        })
    
    tpl_df = pd.DataFrame(tpl_rows)
    
    # 💡 模板编辑器
    edited_tpl_df = st.data_editor(tpl_df, num_rows="dynamic", use_container_width=True)
    
    if st.button("🚀 同步模板配置"):
        new_tpls = {}
        for _, row in edited_tpl_df.iterrows():
            new_tpls[row["模板名称"]] = {
                "pref_vibe": [i.strip() for i in str(row["偏好调性(用逗号隔开)"]).split(",") if i.strip()],
                "pref_target": [i.strip() for i in str(row["偏好人群(用逗号隔开)"]).split(",") if i.strip()],
                "boost": float(row["加权倍率(Boost)"])
            }
        db["templates"] = new_tpls
        save_db(db)
        st.success("模板库已更新！")
