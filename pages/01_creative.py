import streamlit as st
# 📍 导入你的全局组件
from style_manager import apply_pro_style, render_right_warehouse

# --- 1. 记忆与皮肤初始化 ---
# 每个页面都必须检查一下这个“暂存图层”是否存在
if "input_val" not in st.session_state: st.session_state.input_val = ""

st.set_page_config(layout="wide")
apply_pro_style()      # 注入全站皮肤
render_right_warehouse() # 注入镜像仓库组件

# --- 2. 页面核心逻辑 (创意生成) ---
st.title("🎨 创意引擎")

# 这里的输入框值直接绑定 session_state，实现点击仓库即刻导入
st.session_state.input_val = st.text_area(
    "描述你的创意或从右侧点选素材：", 
    value=st.session_state.input_val, 
    height=400
)

# 创意页面特有的功能按钮
c1, c2 = st.columns(2)
with c1:
    if st.button("🪄 随机灵感组合", use_container_width=True):
        st.toast("正在从仓库随机提取素材...")
with c2:
    if st.button("🔥 生成设计草图", type="primary", use_container_width=True):
        st.info("AI 绘图功能接口对接中...")
