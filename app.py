import streamlit as st
import time
from style_manager import apply_pro_style, render_unified_sidebar

# 1. 状态记忆
if "input_val" not in st.session_state: st.session_state.input_val = ""
if "show_right" not in st.session_state: st.session_state.show_right = True

st.set_page_config(layout="wide")
apply_pro_style()
render_unified_sidebar({"主体": 28, "风格": 28, "动作": 15, "氛围": 12})

# --- 布局：中间(4) + 占位(1) + 右侧固定栏(2) ---
if st.session_state.show_right:
    col_main, col_right = st.columns([5, 1.8])
else:
    col_main = st.container()

# 1. 中间核心工作区
with col_main:
    # 顶部开关：做成一个极简的小箭头
    c_t, c_btn = st.columns([10, 1])
    with c_t: st.title("智能入库")
    with c_btn:
        icon = "收起 ❯" if st.session_state.show_right else "❮ 仓库"
        if st.button(icon):
            st.session_state.show_right = not st.session_state.show_right
            st.rerun()

    # 输入框
    user_text = st.text_area("输入或点选标签：", value=st.session_state.input_val, height=500)
    st.session_state.input_val = user_text

    if st.button("🚀 开始 AI 拆解", type="primary", use_container_width=True):
        st.toast("正在处理...")

# 2. 右侧仓库 (受开关控制，视觉上与左边栏对称)
if st.session_state.show_right:
    with col_right:
        st.write("") # 顶开一点距离
        st.caption("📦 仓库管理")
        cat = st.selectbox("类型", ["Subject", "Style"], label_visibility="collapsed")
        
        words = ["日式 old school", "小圆点", "藤蔓", "郁金香", "雏菊"]
        
        st.write("")
        # 📍 极简标签：同一个框，左边加词，右边删词
        for idx, w in enumerate(words):
            # 我们用一个小窍门：在按钮文字里加上一个“空格 + ✕”
            # 这样视觉上它们在一个框里
            c1, c2 = st.columns([4, 1])
            with c1:
                # 点击主文字：加入输入框
                if st.button(f"{w}", key=f"add_{idx}", use_container_width=True):
                    st.session_state.input_val += f" {w}"
                    st.rerun()
            with c2:
                # 点击右侧叉号：执行删除
                if st.button("✕", key=f"del_{idx}", use_container_width=True):
                    st.toast(f"已清理: {w}")
                    st.rerun()
