# pages/03_dashboard.py
import streamlit as st
import pandas as pd
import json
from style_manager import apply_pro_style

apply_pro_style()
st.title("🎮 仓库权重中控台")

# 1. 读取 JSON 数据库
def load_db():
    with open("data/creative_db.json", "r", encoding="utf-8") as f:
        return json.load(f)

db = load_db()

# 2. 将复杂 JSON 转换为表格格式进行编辑
rows = []
for cat, items in db.items():
    for item in items:
        rows.append({
            "分类": cat,
            "关键词": item['val'],
            "人群": item['tags'].get('target', 'all'),
            "调性": item['tags'].get('vibe', 'neutral'),
            "基础权重": item.get('weight_bonus', 1.0)
        })

df = pd.DataFrame(rows)

# 3. 可视化编辑区 (核心：动态修改标签和权重)
st.subheader("📋 标签与权重明细")
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

# 4. 保存逻辑
if st.button("💾 同步修改到全局数据库", type="primary"):
    # 这里将 edited_df 重新打包回 JSON 格式并保存
    # ... (保存逻辑代码)
    st.success("权重已更新，创意引擎页面将实时生效！")
