import streamlit as st
import time
from style_manager import apply_global_frame, render_global_sidebar, render_right_shell

if "input_val" not in st.session_state: st.session_state.input_val = ""
if "ai_tags" not in st.session_state: st.session_state.ai_tags = []

st.set_page_config(layout="wide")
apply_global_frame()
render_global_sidebar()

def app_warehouse_content():
    st.markdown("### 📦 资产仓库")
    st.selectbox("可视化视图", ["Subject", "Style"], label_visibility="collapsed")
    words = ["日式 old school", "小圆点", "非常长的藤蔓纹路换行测试", "郁金香"]
    for idx, w in enumerate(words):
        c1, c2 = st.columns([5, 1.2])
        with c1:
            if st.button(f" {w}", key=f"add_{idx}"):
                st.session_state.input_val += f" {w}"; st.rerun()
        with c2:
            if st.button("✕", key=f"del_{idx}"): st.toast(f"已清理: {w}")

render_right_shell(app_warehouse_content)

# 主业务区
slot_class = "main-canvas-slot" if st.session_state.is_wh_open else "main-canvas-slot"
st.markdown(f'<div class="{slot_class}">', unsafe_allow_html=True)
st.title("⚡ 智能入库")
st.session_state.input_val = st.text_area("提示词编辑", value=st.session_state.input_val, height=300)

if st.session_state.ai_tags:
    st.markdown("#### AI 预览（选择高亮词汇）")
    cols = st.columns(5)
    selected = []
    for i, t in enumerate(st.session_state.ai_tags):
        with cols[i%5]:
            if st.toggle(t, value=True, key=f"pre_{i}"): selected.append(t)

if not st.session_state.ai_tags:
    if st.button("🚀 开始 AI 拆解", type="primary", use_container_width=True):
        with st.status("正在解析结构...") as s:
            time.sleep(1); st.session_state.ai_tags = ["日式", "刺青", "红色"]; s.update(label="完成", state="complete")
        st.rerun()
else:
    if st.button("✅ 一键入库", type="primary", use_container_width=True):
        st.toast("同步成功！"); st.session_state.ai_tags = []; st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
