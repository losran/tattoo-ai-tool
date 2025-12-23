# style_manager.py
import streamlit as st

def apply_pro_style():
    st.markdown("""
    <style>
        /* 1. 📍 Figma 极简深色背景：彻底告别红色 */
        .stApp { background-color: #1E1E1E; color: #E6E6E6; }
        [data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stHeader"] > div:first-child { display: none !important; }

        /* 2. 📍 强制杀掉 Streamlit 原生红色报错框：改为 Figma 灰 */
        .stException, div[data-baseweb="notification"] {
            background-color: #2C2C2C !important;
            color: #AAAAAA !important;
            border: 1px solid #444444 !important;
            border-radius: 6px !important;
        }

        /* 3. 📍 右侧“侧边栏”：Figma 灰面板 */
        [data-testid="column"]:nth-child(2) {
            background-color: #2C2C2C !important;
            border-left: 1px solid #333333 !important;
            padding: 40px 15px !important;
            height: 100vh !important;
            position: fixed !important;
            right: 0; top: 0; z-index: 99;
        }

        /* 4. 📍 极简标签：黑白灰质感 */
        .tag-pill {
            display: flex;
            align-items: center;
            background: #2C2C2C;
            border: 1px solid #444444;
            border-radius: 4px;
            margin-bottom: 6px;
            padding: 2px 10px;
            transition: 0.2s;
            color: #FFFFFF;
        }
        /* 悬停不再变红，变白边 */
        .tag-pill:hover { border-color: #FFFFFF; background: #3E3E3E; }

        /* 5. 📍 按钮样式定制：黑底白字细灰边 */
        div.stButton > button {
            background-color: #2C2C2C !important;
            color: #FFFFFF !important;
            border: 1px solid #444444 !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
        }
        div.stButton > button:hover {
            border-color: #888888 !important;
            background-color: #3E3E3E !important;
        }
        /* 主按钮（Primary）：Figma 蓝作为唯一亮色点缀 */
        div.stButton > button[kind="primary"] {
            background-color: #18A0FB !important;
            border: none !important;
        }

        /* 统一左侧导航字体 */
        [data-testid="stSidebarNav"] ul li div p {
            font-size: 18px !important; font-weight: 500 !important;
            color: #E6E6E6 !important;
        }

        /* 底部统计状态 */
        .metric-footer { border-top: 1px solid #333333; padding-top: 15px; margin-top: 20px; }
        .metric-item { display: flex; justify-content: space-between; font-size: 13px; color: #888888; }
        .metric-item b { color: #FFFFFF; }
    </style>
    """, unsafe_allow_html=True)

def render_unified_sidebar(counts_dict):
    with st.sidebar:
        # 增加 Logo 占位（如果你要在侧边栏顶部放 Logo）
        # st.image("logo.png", width=120) 
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
        st.caption("库存统计")
        for label, val in counts_dict.items():
            st.markdown(f'<div class="metric-item"><span>{label}:</span><b>{val}</b></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
