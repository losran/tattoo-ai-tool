import streamlit as st
from style_manager import apply_pro_style, render_right_warehouse

# --- 1. 记忆与皮肤初始化 ---
if "input_val" not in st.session_state: st.session_state.input_val = ""

st.set_page_config(layout="wide")
apply_pro_style()
render_right_warehouse() # 镜像仓库在这里也同样生效

# --- 2. 页面核心逻辑 (脚本/自动化) ---
st.title("⚡ 自动化工具")

# 输入框同步
st.session_state.input_val = st.text_area(
    "自动化处理文案：", 
    value=st.session_state.input_val, 
    height=300
)

st.divider()
st.markdown("#### 任务流配置")
st.toggle("自动去除重复标签", value=True)
st.toggle("自动翻译为英文 Prompt", value=False)

if st.button("🚀 执行批量处理", type="primary", use_container_width=True):
    with st.status("正在执行自动化脚本...") as s:
        # 这里放你的自动化处理逻辑
        pass
