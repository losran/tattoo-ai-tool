import streamlit as st

def apply_global_frame():
    """强制构建三栏平级物理架构"""
    st.markdown("""
    <style>
        /* 1. 锁死全站背景，干掉顶部多余图标 */
        .stApp { background-color: #0f1014; }
        [data-testid="stHeader"] { display: none !important; }

        /* 2. 📍 右侧平级边栏：物理层级与左侧原生栏一致 */
        .right-sidebar-shell {
            position: fixed;
            right: 0;
            top: 0;
            width: 320px; /* 锁定宽度 */
            height: 100vh;
            background-color: #16171d;
            border-left: 1px solid #262730;
            z-index: 9999; /* 强制最高层级 */
            padding: 40px 15px;
            overflow-y: auto;
        }

        /* 3. 📍 中间业务容器：通过 margin 强制避开两侧墙壁 */
        .main-canvas-slot {
            margin-right: 340px; /* 给右墙留出空隙 */
            padding: 20px;
            max-height: 98vh;
            overflow-y: auto;
        }
        
        /* 当右墙收起时，画布自动拉满 */
        .main-canvas-full {
            margin-right: 20px;
        }

        /* 4. Figma 级标签：Hug contents & 自动换行 */
        .stButton > button {
            width: 100% !important;
            height: auto !important;
            white-space: normal !important;
            word-break: break-all !important;
            text-align: left !important;
            padding: 10px 12px !important;
            background: #1a1b23 !important;
            border: 1px solid #262730 !important;
            border-radius: 6px !important;
            color: #c9d1d9 !important;
        }
        .stButton > button:hover { border-color: #ff4b4b !important; }

        /* 左侧导航 20px 大字对齐 */
        [data-testid="stSidebarNav"] ul li div p { font-size: 20px !important; font-weight: 600 !important; }
    </style>
    """, unsafe_allow_html=True)
