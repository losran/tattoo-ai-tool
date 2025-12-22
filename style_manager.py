# style_manager.py
import streamlit as st

def apply_pro_style():
    st.markdown("""
    <style>
        /* 1. 锁定背景与隐藏杂物 */
        .stApp { background-color: #0f1014; }
        [data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stHeader"] > div:first-child { display: none !important; }

        /* 2. 📍 右侧“侧边栏”：镜像左侧样式 */
        [data-testid="column"]:nth-child(2) {
            background-color: #16171d !important;
            border-left: 1px solid #262730 !important;
            padding: 40px 15px !important; /* 顶开一点，给展开按钮留位 */
            height: 100vh !important;
            position: fixed !important;
            right: 0; top: 0; z-index: 99;
        }

        /* 3. 📍 极简标签：文字和叉号真正在同一个框里 */
        .tag-pill {
            display: flex;
            align-items: center;
            background: #1a1b23;
            border: 1px solid #262730;
            border-radius: 4px;
            margin-bottom: 6px;
            padding: 2px 10px;
            transition: 0.2s;
        }
        .tag-pill:hover { border-color: #ff4b4b; background: #211d1d; }
        
        /* 统一左侧导航字体 */
        [data-testid="stSidebarNav"] ul li div p {
            font-size: 20px !important; font-weight: 600 !important;
        }

        /* 底部统计状态 */
        .metric-footer { border-top: 1px solid #262730; padding-top: 15px; margin-top: 20px; }
        .metric-item { display: flex; justify-content: space-between; font-size: 13px; color: #8b949e; }
    </style>
    """, unsafe_allow_html=True)

def render_unified_sidebar(counts_dict):
    with st.sidebar:
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
        st.caption("库存统计")
        for label, val in counts_dict.items():
            st.markdown(f'<div class="metric-item"><span>{label}:</span><b>{val}</b></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
