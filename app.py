import streamlit as st
import time
from style_manager import apply_global_frame, render_global_warehouse

# --- 1. 状态记忆 ---
if "input_val" not in st.session_state: st.session_state.input_val = ""
if "preview_tags" not in st.session_state: st.session_state.preview_tags = []

st.set_page_config(layout="wide")
apply_global_frame()       # 刷墙（固定层级布局）
render_global_warehouse()  # 立柜（固定镜像仓库）

# --- 2. 侧边栏常驻统计 ---
with st.sidebar:
    st.markdown("<br>" * 10, unsafe_allow_html=True)
    st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
    st.caption("库存统计")
    counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}
    for label, val in counts.items():
        st.markdown(f'<div class="metric-item"><span>{label}:</span><b>{val}</b></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 3. 核心业务区 (智能入库) ---
# 包在 main-slot 里，自动避开右侧仓库
st.markdown('<div class="main-slot">', unsafe_allow_html=True)
st.title("⚡ 智能入库")

# 输入框
st.session_state.input_val = st.text_area(
    "输入提示词：", 
    value=st.session_state.input_val, 
    height=350, 
    placeholder="在此输入需要拆解的内容...",
    label_visibility="collapsed"
)

# AI 预览区：只有拆分后才显示
if st.session_state.preview_tags:
    st.markdown("#### AI 预览 (选择入库词汇)")
    cols = st.columns(5)
    selected_to_cloud = []
    for i, tag in enumerate(st.session_state.preview_tags):
        with cols[i % 5]:
            # 这里的 toggle 实现了你要求的“选择高亮”
            if st.toggle(tag, value=True, key=f"tg_{i}"):
                selected_to_cloud.append(tag)

# 底部功能切换按钮
st.write("")
if not st.session_state.preview_tags:
    if st.button("🚀 开始拆分", type="primary", use_container_width=True):
        with st.status("AI 正在解析标签结构...") as s:
            time.sleep(1)
            st.session_state.preview_tags = ["日式", "纹身", "红色", "old school"]
            s.update(label="拆分完成！", state="complete")
        st.rerun()
else:
    if st.button("✅ 一键入库", type="primary", use_container_width=True):
        st.success(f"已将选中标签同步至右侧仓库！")
        st.session_state.preview_tags = [] # 清空预览流
        time.sleep(1)
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
