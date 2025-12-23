import streamlit as st
import json
import os
import pandas as pd
from openai import OpenAI

# --- 1. 数据地基 (后台逻辑) ---
st.set_page_config(layout="wide", page_title="后台数据中控")

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
            # 自动补全结构
            if "words" not in data: data = {"words": {cat: [] for cat in WAREHOUSE_CONFIG.keys()}, "templates": {}, "prompts": {}}
            if "prompts" not in data:
                data["prompts"] = {
                    "tagger_system": "你是一个纹身审美专家。请分析词汇的视觉调性。",
                    "tagger_user": "分析词汇: '{word}'\n只返回JSON: {'vibe': 'xxx', 'target': 'xxx'}"
                }
            return data
    return {"words": {cat: [] for cat in WAREHOUSE_CONFIG.keys()}, "templates": {}, "prompts": {}}

def save_db(data):
    os.makedirs("data", exist_ok=True)
    with open(JSON_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

db = load_db()

# --- 2. 侧边栏：收纳所有“格格不入”的工具 ---
with st.sidebar:
    st.title("⚙️ 后台专家设置")
    
    with st.expander("🔮 AI 灵魂咒语调教"):
        db["prompts"]["tagger_system"] = st.text_area("系统人格设定", value=db["prompts"]["tagger_system"])
        db["prompts"]["tagger_user"] = st.text_area("分类规则 (须保留 {word})", value=db["prompts"]["tagger_user"], height=200)
        if st.button("💾 保存咒语"):
            save_db(db)
            st.success("咒语已同步")

    with st.expander("🎯 模板与权重加成管理"):
        tpl_data = db.get("templates", {})
        tpl_df = pd.DataFrame([{"名称": k, "倍率": v['boost'], "标签": ",".join(v['pref_vibe'])} for k, v in tpl_data.items()])
        ed_tpl = st.data_editor(tpl_df, num_rows="dynamic")
        if st.button("🚀 同步模板"):
            db["templates"] = {r["名称"]: {"boost": r["倍率"], "pref_vibe": [i.strip() for i in str(r["标签"]).split(",") if i.strip()], "pref_target": ["all"]} for _, r in ed_tpl.iterrows()}
            save_db(db)
            st.rerun()

    with st.expander("⚠️ 系统初始化/修复"):
        if st.button("从旧 TXT 重新搬家"):
            for cat, path in WAREHOUSE_CONFIG.items():
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = [l.strip() for l in f if l.strip()]
                        db["words"][cat] = [{"val": l, "weight_bonus": 1.0, "tags": {"vibe": "general", "target": "all"}} for l in lines]
            save_db(db)
            st.success("搬家完成")

# --- 3. 主页面：极简词库管理 ---
st.title("🏷️ 素材仓库管理")

tab_words = st.container()
with tab_words:
    cat = st.selectbox("当前维度", list(WAREHOUSE_CONFIG.keys()))
    words_list = db["words"].get(cat, [])
    
    # 构建表格
    df = pd.DataFrame([{"词汇": i["val"], "权重": i["weight_bonus"], "调性": i["tags"].get("vibe", "general")} for i in words_list])
    
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    if st.button(f"💾 保存修改并自动打标", type="primary"):
        # 还原数据
        new_words = []
        needs_tagging = []
        
        for _, row in edited_df.iterrows():
            item = {
                "val": row["词汇"], 
                "weight_bonus": float(row["权重"]), 
                "tags": {"vibe": row["调性"], "target": "all"}
            }
            new_words.append(item)
            # 如果是新加的词或是默认标签，加入待洗标名单
            if row["调性"] == "general":
                needs_tagging.append(item)
        
        db["words"][cat] = new_words
        
        # 静默打标
        if needs_tagging:
            ai_client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
            with st.status(f"正在为 {len(needs_tagging)} 个新词进行 AI 审美分类...", expanded=False):
                for item in needs_tagging:
                    prompt = db["prompts"]["tagger_user"].replace("{word}", item["val"])
                    try:
                        res = ai_client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "system", "content": db["prompts"]["tagger_system"]}, {"role": "user", "content": prompt}],
                            response_format={ 'type': 'json_object' }
                        )
                        item["tags"].update(json.loads(res.choices[0].message.content))
                    except: continue
        
        save_db(db)
        st.success("修改已保存，后台已自动完成分类！")
        st.rerun()
