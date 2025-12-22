# style_manager.py
import streamlit as st

def apply_pro_style():
    st.markdown("""
    <style>
        /* 1. 📍 物理抹除顶部所有无用图标 (Share, Star, GitHub等) */
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0) !important;
        }
        [data-testid="stHeader"] > div:first-child {
            display: none !important; /* 彻底隐藏那一排小图标 */
        }

        /* 2. 锁定全局背景 */
        .stApp { background-color: #0f1014; }

        /* 3. 放大左侧导航文字 */
        [data-testid="stSidebarNav"] ul li div p {
            font-size: 20px !important; 
            font-weight: 600 !important;
            color: #c9d1d9 !important;
        }

        /* 4. 📍 右侧伪装栏：强制置顶对齐，无视顶部间距 */
        [data-testid="column"]:nth-child(2) {
            background-color: #16171d !important;
            border-left: 1px solid #262730 !important;
            padding: 20px 15px !important;
            height: 100vh !important;
            position: fixed !important;
            right: 0;
            top: 0;
            z-index: 100;
        }

        /* 5. 📍 组合标签：文字和叉号合并为一个视觉整体 */
        .stButton > button {
            border: 1px solid #262730 !important;
            background: #1a1b23 !important;
            color: #c9d1d9 !important;
            width: 100% !important;
            padding: 5px 12px !important;
            text-align: left !important;
            border-radius: 4px !important;
        }
        .stButton > button:hover {
            border-color: #ff4b4b !important;
        }

        /* 侧边栏底部统计 */
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
