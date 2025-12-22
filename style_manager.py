import streamlit as st

def apply_pro_style():
    st.markdown("""
    <style>
        .stApp { background-color: #0f1014; }
        [data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stHeader"] > div:first-child { display: none !important; }

        /* 📍 导航文字放大至 20px */
        [data-testid="stSidebarNav"] ul li div p { font-size: 20px !important; font-weight: 600 !important; color: #c9d1d9 !important; }

        /* 📍 右侧镜像侧边栏：宽度锁定，镜像收起 */
        [data-testid="column"]:nth-child(2) {
            background-color: #16171d !important;
            border-left: 1px solid #262730 !important;
            padding: 40px 15px !important;
            height: 100vh !important;
            position: fixed !important;
            right: 0; top: 0; z-index: 99;
            max-width: 320px !important;
        }

        /* 📍 Figma 式标签：自动换行 (Hug contents) */
        .stButton > button {
            width: 100% !important; height: auto !important; padding: 6px 12px !important;
            white-space: normal !important; word-break: break-all !important;
            text-align: left !important; border: 1px solid #262730 !important;
            background: #1a1b23 !important; color: #c9d1d9 !important;
        }
        .stButton > button:hover { border-color: #ff4b4b !important; }

        /* 底部统计状态 */
        .metric-footer { border-top: 1px solid #262730; padding-top: 15px; margin-top: 30px; }
        .metric-item { display: flex; justify-content: space-between; font-size: 13px; color: #8b949e; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)
