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
            data = json.load(f)
            # 💡 核心修复：如果发现是旧格式，自动强制升级为新格式
            if "words" not in data:
                return {
                    "words": {cat: [] for cat in WAREHOUSE_CONFIG.keys()},
                    "templates": {"完全随机模式": {"pref_vibe": [], "pref_target": [], "boost": 1.0}}
                }
            return data
    return {"words": {cat: [] for cat in WAREHOUSE_CONFIG.keys()}, "templates": {}}

def save_db(data):
    os.makedirs("data", exist_ok=True)
    with open(JSON_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

db = load_db()

st.title("🎮 仓库权重中控台")

# --- 2. 搬家工具 (点击此处修复 KeyError) ---
with st.expander("🛠️ 修复与初始化：将 TXT 导入新版 JSON", expanded=True):
    st.warning("如果你看到 KeyError 报错，请点击下方按钮重新初始化。")
    if st.button("🚀 执行初始化/数据修复"):
        new_db = {
            "words": {cat: [] for cat in WAREHOUSE_CONFIG.keys()},
            "templates": {"少女心系列 (Sell_to_girls)": {"pref_vibe": ["healing", "cute"], "pref_target": ["female"], "boost": 6.0}}
        }
        for cat, path in WAREHOUSE_CONFIG.items():
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    lines = [l.strip() for l in f if l.strip()]
                    new_db["words"][cat] = [{"val": l, "weight_bonus": 1.0, "tags": {"vibe": "general", "target": "all"}} for l in lines]
        save_db(new_db)
        st.success("数据已成功升级为新格式！")
        st.rerun()

# --- 3. 核心调控区 ---
tab_words, tab_templates = st.tabs(["🏷️ 词库与权重调控", "🎯 意图模板配置"])

with tab_words:
    category = st.selectbox("选择维度", list(WAREHOUSE_CONFIG.keys()))
    words_list = db["words"].get(category, [])
    if words_list:
        df = pd.DataFrame([{"词汇": i["val"], "权重": i["weight_bonus"], "调性": i["tags"]["vibe"]} for i in words_list])
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button(f"💾 保存 {category} 修改"):
            db["words"][category] = [{"val": r["词汇"], "weight_bonus": float(r["权重"]), "tags": {"vibe": r["调性"], "target": "all"}} for _, r in edited_df.iterrows()]
            save_db(db)
            st.success("保存成功")

with tab_templates:
    st.info("在这里可以管理不同模板的加分逻辑。")
    # 此处省略部分模板编辑逻辑，重点先保住词库可用
