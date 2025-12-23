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

# --- 修改 load_db 的返回结构 ---
def load_db():
    if os.path.exists(JSON_DB_PATH):
        with open(JSON_DB_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 补齐字段
            if "prompts" not in data:
                data["prompts"] = {
                    "tagger_system": "你是一个纹身审美专家。请分析词汇的视觉调性。",
                    "tagger_user": "分析词汇: '{word}'\n1. 调性(vibe): 从[cute, healing, dark, hardcore, minimalist, cyberpunk, geometric]选一个最贴切的。\n2. 人群(target): 从[male, female, unisex]选一个。\n只返回JSON: {'vibe': 'xxx', 'target': 'xxx'}"
                }
            return data
    return {"words": {}, "templates": {}, "prompts": {}}

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

# --- 定位：在“执行初始化/数据修复”按钮的 if 逻辑结束后插入 ---
st.divider()
st.subheader("🤖 AI 自动语义洗标")
st.caption("让 AI 扫描全库，自动根据词义填充调性标签（vibe）和人群倾向（target）")

if st.button("🪄 启动 AI 一键全量打标", type="secondary", use_container_width=True):
    from openai import OpenAI
    # 初始化客户端 (确保 secrets 里有 key)
    ai_client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
    
    with st.spinner("AI 正在解析词库灵魂... 请稍候..."):
        db = load_db()
        words_structure = db.get("words", {})
        count = 0
        
        for cat, items in words_structure.items():
            for item in items:
                # 只对还是 general 的词进行处理，避免浪费次数
                if item["tags"].get("vibe") == "general":
                    word = item["val"]
                    
                    # 💡 这是调教 AI 的核心咒语
                    sys_prompt = "你是一个纹身审美专家。请分析词汇的视觉调性。"
                    user_prompt = f"""分析词汇: '{word}'
                    1. 调性(vibe): 从[cute, healing, dark, hardcore, minimalist, cyberpunk, geometric]选一个最贴切的。
                    2. 人群(target): 从[male, female, unisex]选一个。
                    只返回JSON: {{"vibe": "xxx", "target": "xxx"}}"""
                    
                    try:
                        response = ai_client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[
                                {"role": "system", "content": sys_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            response_format={ 'type': 'json_object' }
                        )
                        new_tags = json.loads(response.choices[0].message.content)
                        item["tags"].update(new_tags)
                        count += 1
                    except Exception as e:
                        continue
        
        save_db(db)
        st.success(f"✅ AI 进化完成！已自动识别并更新 {count} 个词汇的标签。")
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
    # --- 定位：替换 with tab_templates: 内部的所有内容 ---

    st.subheader("🎯 意图模板可视化调控")
    
    # 获取现有模板
    tpl_data = db.get("templates", {})
    
    # 格式化成表格，方便你编辑
    tpl_rows = []
    for name, cfg in tpl_data.items():
        tpl_rows.append({
            "模板名称": name,
            "偏好标签(用逗号隔开)": ",".join(cfg.get("pref_vibe", [])),
            "权重放大倍率": cfg.get("boost", 1.0)
        })
    
    df_tpl = pd.DataFrame(tpl_rows)
    
    # 💡 在这里直接改、直接加行，就是加模板！
    edited_tpl = st.data_editor(df_tpl, num_rows="dynamic", use_container_width=True)
    
    if st.button("🚀 确认并同步模板配置", type="primary"):
        new_templates = {}
        for _, row in edited_tpl.iterrows():
            new_templates[row["模板名称"]] = {
                "pref_vibe": [i.strip() for i in str(row["偏好标签(用逗号隔开)"]).split(",") if i.strip()],
                "pref_target": ["unisex"], # 默认中性
                "boost": float(row["权重放大倍率"])
            }
        db["templates"] = new_templates
        save_db(db)
        st.success("配置已同步！去创意引擎看看下拉框吧。")
