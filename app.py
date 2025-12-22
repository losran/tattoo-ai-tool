import streamlit as st
import time
from style_manager import apply_pro_style, render_unified_sidebar

# 基础配置
st.set_page_config(layout="wide", page_title="Alien Mood Central")
apply_pro_style()

# 常驻统计数据
counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}
render_unified_sidebar(counts)

# 模拟数据
WAREHOUSE = {"Subject": ["日式 old school", "小圆点", "藤蔓", "郁金香", "雏菊"]}

# --- 布局：中间操作(5) + 右侧固定仓库(2) ---
col_main, col_right = st.columns([5, 2])

# 1. 中间主操作区 (可滚动)
with col_main:
    st.title("智能入库")
    
    # 这里的输入框现在是核心焦点
    if "input_val" not in st.session_state:
        st.session_state.input_val = ""
        
    user_input = st.text_area(
        "输入或点选标签：", 
        value=st.session_state.input_val,
        height=450, 
        key="main_editor"
    )
    # 实时更新状态，方便右侧按钮读取
    st.session_state.input_val = user_input

    if st.button("🚀 开始拆解", type="primary", use_container_width=True):
        st.toast("AI 正在工作...")

# 2. 右侧固定栏：仓库管理
with col_right:
    # 模拟“向右收起”：用 Streamlit 的折叠容器实现最稳妥
    with st.expander("📦 仓库管理 (点击展开/收起)", expanded=True):
        cat = st.selectbox("分类", list(WAREHOUSE.keys()), label_visibility="collapsed")
        words = WAREHOUSE.get(cat, [])
        
        st.divider()
        
        # 极简交互列表
        for idx, w in enumerate(words):
            c1, c2 = st.columns([5, 1])
            
            # 📍 点文字：直接加入输入框
            with c1:
                if st.button(f" {w}", key=f"add_{idx}", use_container_width=True):
                    if st.session_state.input_val:
                        st.session_state.input_val += f" {w}"
                    else:
                        st.session_state.input_val = w
                    st.rerun()
            
            # 📍 点叉号：直接删除
            with c2:
                if st.button("✕", key=f"del_{idx}", use_container_width=True):
                    # 这里放你原本的删除逻辑
                    st.toast(f"已清理: {w}")
                    time.sleep(0.3)
                    st.rerun()
