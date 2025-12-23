# style_manager.py
import streamlit as st

def apply_pro_style():
    st.markdown("""
    <style>
        /* 1. 🎨 Figma 核心底色：深炭灰背景 */
        .stApp { 
            background-color: #121212 !important; 
            color: #E6E6E6 !important; 
        }
        [data-testid="stHeader"] { background: transparent !important; }

        /* 2. 🚫 物理封印红色报错：强行改为 Figma 警告色（深褐灰） */
        .stException, div[data-baseweb="notification"], .stAlert, [data-testid="stNotification"] {
            background-color: #2D2D2D !important;
            color: #AAAAAA !important;
            border: 1px solid #444444 !important;
            border-radius: 8px !important;
        }
        /* 针对错误堆栈的文字颜色也强制变灰 */
        .stException pre { color: #888888 !important; }

        /* 3. 📍 右侧面板：Figma 图层面板色 */
        [data-testid="column"]:nth-child(2) {
            background-color: #1E1E1E !important;
            border-left: 1px solid #333333 !important;
            padding: 40px 15px !important;
            height: 100vh !important;
            position: fixed !important;
            right: 0; top: 0; z-index: 99;
        }

        /* 4. 🏷️ 极简标签：深灰背景 + 极细白边 */
        .tag-pill {
            display: flex;
            align-items: center;
            background: #252525 !important;
            border: 1px solid #3A3A3A !important;
            border-radius: 4px !important;
            margin-bottom: 6px !important;
            padding: 4px 12px !important;
            color: #CCCCCC !important;
        }
        .tag-pill:hover { border-color: #888888 !important; background: #2A2A2A !important; }

        /* 5. 🔘 按钮：Figma 风格黑底白字 */
        div.stButton > button {
            background-color: #2C2C2C !important;
            color: #FFFFFF !important;
            border: 1px solid #444444 !important;
            border-radius: 6px !important;
        }
        div.stButton > button:hover { 
            border-color: #18A0FB !important; /* 仅保留 Figma 蓝作为交互反馈 */
            background-color: #333333 !important; 
        }
        
        /* ⚡ 主按钮：强制黑白灰化，或者保留极克制的蓝色 */
        div.stButton > button[kind="primary"] {
            background-color: #18A0FB !important;
            color: white !important;
            border: none !important;
        }

        /* 6. ✍️ 输入框：深沉嵌入感 */
        .stTextArea textarea, .stTextInput input {
            background-color: #1E1E1E !important;
            color: #FFFFFF !important;
            border: 1px solid #333333 !important;
            border-radius: 8px !important;
        }

        /* 📊 底部统计：低调暗灰 */
        .metric-footer { border-top: 1px solid #333333; padding-top: 15px; margin-top: 20px; }
        .metric-item { display: flex; justify-content: space-between; font-size: 13px; color: #666666; }
        .metric-item b { color: #BBBBBB; }
    </style>
    """, unsafe_allow_html=True)

def render_unified_sidebar(counts_dict):
    with st.sidebar:
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
        st.caption("📦 仓库快照")
        for label, val in counts_dict.items():
            st.markdown(f'<div class="metric-item"><span>{label}:</span><b>{val}</b></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
