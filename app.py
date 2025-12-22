import streamlit as st
import time
from style_manager import apply_pro_style

# --- 1. 核心功能逻辑与记忆 ---
if "input_val" not in st.session_state: st.session_state.input_val = ""
if "is_open" not in st.session_state: st.session_state.is_open = True
if "ai_preview_tags" not in st.session_state: st.session_state.ai_preview_tags = []

st.set_page_config(layout="wide")
apply_pro_style()

# 模拟 GitHub 数据库逻辑 (请在此处保留你真实的 get/save 函数)
def get_warehouse_data(cat):
    return ["日式 old school", "小圆点", "藤蔓", "郁金香", "雏菊"]

# --- 2. 侧边栏常驻统计 ---
with st.sidebar:
    st.markdown("<br>" * 10, unsafe_allow_html=True)
    st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
    st.caption("库存统计")
    counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}
    for label, val in counts.items():
        st.markdown(f'<div class="metric-item"><span>{label}:</span><b>{val}</b></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 3. 布局与开关 ---
btn_col1, btn_col2 = st.columns([12, 1])
with btn_col2:
    icon = "❯" if st.session_state.is_open else "❮ 仓库"
    if st.button(icon):
        st.session_state.is_open = not st.session_state.is_open
        st.rerun()

if st.session_state.is_open:
    col_main, col_right = st.columns([5, 1.8])
else:
    col_main = st.container()

# --- 4. 中间主操作区：智能拆分 ---
with col_main:
    st.title("⚡ 智能入库")
    
    # 输入栏 (支持手打与点选同步)
    user_text = st.text_area("在此输入提示词：", value=st.session_state.input_val, height=350, label_visibility="collapsed")
    st.session_state.input_val = user_text

    # AI 拆分预览区 (显示在输入栏下方)
    if st.session_state.ai_preview_tags:
        st.markdown("#### AI 预览 (选择需要入库的标签)")
        selected_tags = []
        tag_cols = st.columns(5)
        for i, t in enumerate(st.session_state.ai_preview_tags):
            with tag_cols[i % 5]:
                if st.toggle(t, value=True, key=f"pre_{i}"):
                    selected_tags.append(t)

    # 底部核心按钮：拆分 vs 一键入库
    st.write("")
    if not st.session_state.ai_preview_tags:
        if st.button("🚀 开始拆分 (显示 AI 进度)", type="primary", use_container_width=True):
            with st.status("AI 正在拆分主体与单词...") as s:
                time.sleep(1)
                st.session_state.ai_preview_tags = ["日式", "纹身", "红色", "old school"]
                s.update(label="拆分完成！", state="complete")
            st.rerun()
    else:
        if st.button("📥 一键入库 (同步至云端)", type="primary", use_container_width=True):
            st.success(f"已将 {len(selected_tags)} 个标签移至右侧仓库")
            st.session_state.ai_preview_tags = [] # 清空预览
            time.sleep(1)
            st.rerun()

# --- 5. 右侧仓库管理：可视化下拉 ---
if st.session_state.is_open:
    with col_right:
        st.markdown("### 📦 仓库管理")
        cat = st.selectbox("可视化管理方式", ["Subject", "Style", "Action"], label_visibility="collapsed")
        words = get_warehouse_data(cat)
        
        st.divider()
        for idx, w in enumerate(words):
            t_col, x_col = st.columns([5, 1.2], gap="small")
            with t_col:
                if st.button(f" {w}", key=f"lib_add_{idx}", use_container_width=True):
                    st.session_state.input_val += f" {w}"
                    st.rerun()
            with x_col:
                if st.button("✕", key=f"lib_del_{idx}", use_container_width=True):
                    st.toast(f"已从云库删除: {w}")
                    st.rerun()
