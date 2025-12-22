import streamlit as st

def apply_global_frame():
    """镜像物理布局：左右死锁，中间滚动"""
    st.markdown("""
    <style>
        .stApp { background-color: #0f1014; }
        [data-testid="stHeader"] { display: none !important; }

        /* 📍 1. 物理层级：强制让右侧列变为“右侧边栏” */
        div[data-testid="column"]:nth-child(2) {
            position: fixed !important;
            right: 0;
            top: 0;
            width: 320px !important;
            height: 100vh !important;
            background-color: #16171d !important;
            border-left: 1px solid #262730 !important;
            z-index: 1000 !important;
            padding: 40px 15px !important;
            overflow-y: auto !important;
        }

        /* 📍 2. 中间槽位：强制留出右边距，不被仓库遮挡 */
        div[data-testid="column"]:nth-child(1) {
            margin-right: 330px !important;
            max-height: 95vh !important;
            overflow-y: auto !important;
        }

        /* 📍 3. Figma 标签逻辑：Hug contents 且自动换行 */
        .stButton > button {
            width: 100% !important; height: auto !important;
            white-space: normal !important; word-break: break-all !important;
            text-align: left !important; background: #1a1b23 !important;
            border: 1px solid #262730 !important; color: #c9d1d9 !important;
            padding: 8px 12px !important; border-radius: 6px !important;
        }
        .stButton > button:hover { border-color: #ff4b4b !important; }

        /* 左侧导航文字放大 */
        [data-testid="stSidebarNav"] ul li div p { font-size: 20px !important; font-weight: 600 !important; }
        .metric-footer { border-top: 1px solid #262730; padding-top: 15px; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

def render_global_sidebar():
    """左侧常驻统计"""
    with st.sidebar:
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
        st.caption("库存统计")
        counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}
        for label, val in counts.items():
            st.markdown(f'<div style="display:flex; justify-content:space-between; font-size:13px; color:#8b949e; margin-bottom:6px;"><span>{label}:</span><b>{val}</b></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
