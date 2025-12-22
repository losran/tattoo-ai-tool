import streamlit as st
from style_manager import apply_pro_style, render_unified_sidebar

# 记忆初始化
if "input_val" not in st.session_state: st.session_state.input_val = ""
if "show_warehouse" not in st.session_state: st.session_state.show_warehouse = True

st.set_page_config(layout="wide", initial_sidebar_state="expanded")
apply_pro_style()
render_unified_sidebar({"主体": 28, "风格": 28, "动作": 15, "氛围": 12})

# --- 核心布局计算 ---
if st.session_state.show_warehouse:
    col_main, col_right = st.columns([5, 1.8])
else:
    col_main = st.container()

# 1. 中间主工作区
with col_main:
    st.title("智能入库")
    
    # 📍 如果仓库被收起了，这里显示一个微小的“展开”入口
    if not st.session_state.show_warehouse:
        if st.button("⬅ 展开仓库", key="expand_btn"):
            st.session_state.show_warehouse = True
            st.rerun()

    user_text = st.text_area("输入或点选标签：", value=st.session_state.input_val, height=550)
    st.session_state.input_val = user_text
    st.button("🚀 开始 AI 拆解", type="primary", use_container_width=True)

# 2. 右侧固定仓库 (受开关控制)
if st.session_state.show_warehouse:
    with col_right:
        # 📍 重点：把“仓库标题”和“收起按钮”做在同一行，完美对齐
        c_title, c_close = st.columns([4, 1])
        with c_title:
            st.markdown("### 📦 仓库管理")
        with c_close:
            # 使用极简的箭头作为收起按钮
            if st.button("❯", help="点击收起"):
                st.session_state.show_warehouse = False
                st.rerun()
        
        cat = st.selectbox("类型", ["Subject", "Style"], label_visibility="collapsed")
        
        # 模拟数据
        words = ["日式 old school", "小圆点", "藤蔓", "郁金香", "雏菊"]
        
        st.write("")
        # 📍 极简组合交互：同一个背景框内的点选与删除
        for idx, w in enumerate(words):
            # 将文字和叉号放在两个无缝连接的列中
            tag_col, x_col = st.columns([5, 1])
            with tag_col:
                if st.button(f"{w}", key=f"add_{idx}", use_container_width=True):
                    st.session_state.input_val += f" {w}"
                    st.rerun()
            with x_col:
                if st.button("✕", key=f"del_{idx}", use_container_width=True):
                    st.toast(f"已移除: {w}")
                    st.rerun()
