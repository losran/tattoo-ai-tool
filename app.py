import streamlit as st
import time

# --- 1. 记忆中控 (Session State) ---
if "input_val" not in st.session_state: st.session_state.input_val = ""
if "is_open" not in st.session_state: st.session_state.is_open = True

# --- 2. 视觉底层 (CSS 注入 - 解决 Figma 式自适应与自动换行) ---
def apply_figma_style():
    st.markdown("""
    <style>
        /* 1. 锁死背景与隐藏顶部图标 */
        .stApp { background-color: #0f1014; }
        [data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stHeader"] > div:first-child { display: none !important; }

        /* 2. 📍 重点：修复“字飞散”——实现 Hug Contents */
        /* 强制让按钮变为行内块，并允许换行 */
        .stButton > button {
            width: auto !important;
            height: auto !important;
            padding: 4px 10px !important;
            white-space: normal !important; /* 允许换行 */
            text-align: left !important;
            border: 1px solid #262730 !important;
            background: #1a1b23 !important;
            color: #c9d1d9 !important;
            font-size: 14px !important;
        }
        
        /* 3. 📍 标签一体化：文字按钮和叉号按钮的视觉缝合 */
        /* 去掉中间的间距和圆角，让它们看起来像一个框 */
        div[data-testid="column"]:nth-child(1) button {
            border-right: none !important;
            border-top-right-radius: 0 !important;
            border-bottom-right-radius: 0 !important;
        }
        div[data-testid="column"]:nth-child(2) button {
            border-left: none !important;
            border-top-left-radius: 0 !important;
            border-bottom-left-radius: 0 !important;
            color: #4b5563 !important;
        }
        
        /* 4. 右侧镜像栏对齐 */
        [data-testid="column"]:nth-child(2) {
            background-color: #16171d !important;
            border-left: 1px solid #262730 !important;
            padding: 40px 15px !important;
            height: 100vh !important;
            position: fixed !important;
            right: 0; top: 0; z-index: 99;
            max-width: 320px !important; /* 📍 锁定宽度，防止比例放大时散架 */
        }

        /* 5. 导航放大 */
        [data-testid="stSidebarNav"] ul li div p { font-size: 20px !important; font-weight: 600 !important; }
        
        /* 底部统计状态 */
        .metric-footer { border-top: 1px solid #262730; padding-top: 15px; margin-top: 30px; }
        .metric-item { display: flex; justify-content: space-between; font-size: 13px; color: #8b949e; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 页面构建 ---
st.set_page_config(layout="wide")
apply_figma_style()

# 渲染侧边栏统计
with st.sidebar:
    st.markdown("<br>" * 10, unsafe_allow_html=True)
    st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
    st.caption("库存统计")
    counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}
    for label, val in counts.items():
        st.markdown(f'<div class="metric-item"><span>{label}:</span><b>{val}</b></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 📍 右上角收起/展开开关 (镜像原生逻辑) ---
btn_col1, btn_col2 = st.columns([12, 1])
with btn_col2:
    icon = "❯" if st.session_state.is_open else "❮ 仓库"
    if st.button(icon):
        st.session_state.is_open = not st.session_state.is_open
        st.rerun()

# --- 4. 核心布局 ---
if st.session_state.is_open:
    col_main, col_right = st.columns([5, 1.8])
else:
    col_main = st.container()

# 中间操作区 (Figma 画布感)
with col_main:
    st.title("🎨 智能入库")
    user_text = st.text_area("提示词编辑", value=st.session_state.input_val, height=550, label_visibility="collapsed")
    st.session_state.input_val = user_text
    st.button("🚀 开始 AI 拆解", type="primary", use_container_width=True)

# 右侧仓库管理 (受开关控制)
if st.session_state.is_open:
    with col_right:
        st.markdown("### 📦 仓库管理")
        cat = st.selectbox("类型", ["Subject", "Style"], label_visibility="collapsed")
        
        # 模拟长短不一的文字，测试“Hug contents”换行
        words = ["日式 old school", "小圆点", "非常长的藤蔓刺青纹路展示", "郁金香", "雏菊"]
        
        st.write("")
        for idx, w in enumerate(words):
            # 📍 文字和叉在同一个视觉框
            t_col, x_col = st.columns([6, 1.2], gap="small")
            with t_col:
                if st.button(f" {w}", key=f"add_{idx}", use_container_width=True):
                    st.session_state.input_val += f" {w}"
                    st.rerun()
            with x_col:
                if st.button("✕", key=f"del_{idx}", use_container_width=True):
                    st.toast(f"已清理: {w}")
                    st.rerun()
