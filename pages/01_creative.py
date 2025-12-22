import streamlit as st
import random, time
from style_manager import apply_global_frame, render_global_sidebar, render_right_shell

if "input_val" not in st.session_state: st.session_state.input_val = ""

st.set_page_config(layout="wide")
apply_global_frame()
render_global_sidebar()

def creative_warehouse():
    st.markdown("### 📦 素材库")
    words = ["机械感", "浮世绘", "极简细线", "重彩写实"]
    for idx, w in enumerate(words):
        if st.button(f" {w}", key=f"cr_{idx}"):
            st.session_state.input_val += f" {w}"; st.rerun()

render_right_shell(creative_warehouse)

st.markdown('<div class="main-canvas-slot">', unsafe_allow_html=True)
st.title("🎨 创意引擎")
st.session_state.input_val = st.text_area("描述创意", value=st.session_state.input_val, height=400)

c1, c2 = st.columns(2)
with c1:
    if st.button("🪄 随机灵感组合", use_container_width=True):
        st.session_state.input_val += f" {random.choice(['金属', '荧光', '水墨'])}"; st.rerun()
with c2:
    if st.button("🔥 生成设计草图", type="primary", use_container_width=True):
        with st.status("联想中..."): time.sleep(1)
st.markdown('</div>', unsafe_allow_html=True)
