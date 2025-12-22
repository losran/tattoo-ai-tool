import streamlit as st
from style_manager import apply_pro_style, render_unified_sidebar

# 初始化状态
if "input_val" not in st.session_state: st.session_state.input_val = ""
if "is_open" not in st.session_state: st.session_state.is_open = True

st.set_page_config(layout="wide", initial_sidebar_state="expanded")
apply_pro_style()
render_unified_sidebar({"主体": 28, "风格": 28, "动作": 15, "氛围": 12})

# --- 📍 顶层开关：永远固定在右上角 ---
# 我们利用 col_main 之外的容器来放置这个绝对定位的开关
btn_col1, btn_col2 = st.columns([12, 1])
with btn_col2:
    # 这个按钮在视觉上会出现在仓库的顶端对齐处
    icon = "❯" if st.session_state.is_open else "❮ 仓库"
    if st.button(icon, help="切换仓库显示"):
        st.session_state.is_open = not st.session_state.is_open
        st.rerun()

# --- 核心布局：5:2 镜像比例 ---
if st.session_state.is_open:
    col_main, col_right = st.columns([5, 1.8])
else:
    col_main = st.container()

# 1. 中间主工作区
with col_main:
    st.title("🎨 智能入库")
    # 高度根据屏幕自适应撑满
    user_text = st.text_area("提示词编辑区", value=st.session_state.input_val, height=580, label_visibility="collapsed")
    st.session_state.input_val = user_text
    st.button("🚀 开始 AI 拆解", type="primary", use_container_width=True)

# 2. 右侧固定栏 (镜像侧边栏)
if st.session_state.is_open:
    with col_right:
        st.markdown("### 📦 仓库管理")
        cat = st.selectbox("类型", ["Subject", "Style"], label_visibility="collapsed")
        
        words = ["日式 old school", "小圆点", "藤蔓", "郁金香", "雏菊"]
        
        st.write("")
        # 📍 标签交互：文字和叉号合并在一个视觉框内
        for idx, w in enumerate(words):
            # 用一个极细的 column 组合来模拟“同一个框”
            t_col, x_col = st.columns([6, 1.2])
            with t_col:
                # 文字按钮：去掉右边框
                if st.button(f" {w}", key=f"add_{idx}", use_container_width=True):
                    st.session_state.input_val += f" {w}"
                    st.rerun()
            with x_col:
                # 叉号按钮：去掉左边框
                if st.button("✕", key=f"del_{idx}", use_container_width=True):
                    st.toast(f"已清理: {w}")
                    st.rerun()
