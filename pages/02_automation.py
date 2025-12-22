import streamlit as st
import time
from style_manager import apply_global_frame, render_global_sidebar, render_right_shell

if "input_val" not in st.session_state: st.session_state.input_val = ""

st.set_page_config(layout="wide")
apply_global_frame()
render_global_sidebar()

render_right_shell(lambda: st.markdown("### 📦 资产列表"))

st.markdown('<div class="main-canvas-slot">', unsafe_allow_html=True)
st.title("⚡ 自动化工具")
st.session_state.input_val = st.text_area("处理内容", value=st.session_state.input_val, height=250)

st.toggle("自动清理重复项", value=True)
st.toggle("转为 MJ Prompt", value=False)

if st.button("🚀 执行自动化脚本", type="primary", use_container_width=True):
    with st.status("运行中..."): time.sleep(1)
    st.balloons()
st.markdown('</div>', unsafe_allow_html=True)
