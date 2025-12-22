import streamlit as st
import random, time
from style_manager import apply_global_frame, render_global_sidebar

# --- 1. 记忆初始化 ---
if "input_val" not in st.session_state: st.session_state.input_val = ""
if "is_warehouse_open" not in st.session_state: st.session_state.is_warehouse_open = True

st.set_page_config(layout="wide")
apply_global_frame()       # 刷墙（固定右侧物理层级）
render_global_sidebar()    # 立柱（左侧常驻统计）

# --- 2. 顶层开关：镜像原生闭合逻辑 ---
btn_col1, btn_col2 = st.columns([12, 1.2])
with btn_col2:
    icon = "❯" if st.session_state.is_warehouse_open else "❮ 仓库"
    if st.button(icon, key="creative_toggle"):
        st.session_state.is_warehouse_open = not st.session_state.is_warehouse_open
        st.rerun()

# --- 3. 核心平级布局 ---
if st.session_state.is_warehouse_open:
    col_main, col_right = st.columns([5, 1.8]) # 这里的 col_right 会被 CSS 强制固定
else:
    col_main = st.container()

# --- 4. 中间业务：创意灵感区 ---
with col_main:
    st.title("🎨 创意引擎")
    st.info("💡 灵感匮乏？从右侧仓库点选素材，或在下方直接构建提示词。")
    
    # 绑定全局记忆，实现右侧点选导入
    st.session_state.input_val = st.text_area("创意编辑区", value=st.session_state.input_val, height=450, label_visibility="collapsed")

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🪄 随机灵感组合", use_container_width=True):
            tags = ["机械", "复古", "极简", "重彩"]
            picked = random.choice(tags)
            st.session_state.input_val += f" {picked}"
            st.toast(f"注入灵感: {picked}")
            time.sleep(0.5)
            st.rerun()
    with c2:
        if st.button("🔥 生成创意方案", type="primary", use_container_width=True):
            with st.status("正在联想视觉方案...") as s:
                time.sleep(1)
                s.update(label="方案已生成！", state="complete")

# --- 5. 右侧镜像仓库：层级平齐、物理固定 ---
if st.session_state.is_warehouse_open:
    with col_right:
        st.markdown("### 📦 素材仓库")
        st.selectbox("分类选择", ["Subject", "Style"], label_visibility="collapsed")
        
        words = ["old school", "日式传统", "非常长的藤蔓纹路换行测试", "浮世绘"]
        st.write("")
        for idx, w in enumerate(words):
            # 极简组合：左边加词，右边删词
            t_col, x_col = st.columns([5, 1.2], gap="small")
            with t_col:
                if st.button(f" {w}", key=f"cr_add_{idx}", use_container_width=True):
                    st.session_state.input_val += f" {w}"
                    st.rerun()
            with x_col:
                if st.button("✕", key=f"cr_del_{idx}"):
                    st.toast(f"已清理: {w}")
                    st.rerun()
