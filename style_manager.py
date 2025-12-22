import streamlit as st

def apply_global_frame():
    """镜像物理布局：左右死锁，中间滚动，标签自适应"""
    st.markdown("""
    <style>
        /* 1. 全局底色与隐藏多余元素 */
        .stApp { background-color: #0f1014; }
        [data-testid="stHeader"] { display: none !important; }

        /* 2. 📍 核心：强制将右侧列物理钉死在屏幕右侧 */
        div[data-testid="column"]:nth-child(2) {
            position: fixed !important;
            right: 0 !important;
            top: 0 !important;
            width: 320px !important; /* 锁定宽度，防止乱飞 */
            height: 100vh !important;
            background-color: #16171d !important;
            border-left: 1px solid #262730 !important;
            z-index: 1000 !important;
            padding: 40px 15px !important;
            overflow-y: auto !important;
        }

        /* 3. 📍 核心：中间业务区强制避让左右两堵“墙” */
        div[data-testid="column"]:nth-child(1) {
            margin-right: 330px !important; /* 为右侧仓库留出物理空间 */
            max-height: 95vh !important;
            overflow-y: auto !important;
            padding-bottom: 50px !important;
        }

        /* 4. 📍 Figma 标签逻辑：Hug contents 且自动换行 */
        .stButton > button {
            width: 100% !important; 
            height: auto !important;
            white-space: normal !important; /* 强制换行 */
            word-break: break-all !important;
            text-align: left !important; 
            background: #1a1b23 !important;
            border: 1px solid #262730 !important; 
            color: #c9d1d9 !important;
            padding: 8px 12px !important; 
            border-radius: 6px !important;
        }
        .stButton > button:hover { border-color: #ff4b4b !important; }

        /* 左侧导航文字放大 */
        [data-testid="stSidebarNav"] ul li div p { font-size: 20px !important; font-weight: 600 !important; }
        
        /* 侧边栏底部统计对齐 */
        .metric-footer { border-top: 1px solid #262730; padding-top: 15px; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

def render_global_sidebar():
    """渲染左侧原生导航底部的统计状态"""
    with st.sidebar:
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
        st.caption("库存统计")
        counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}
        for label, val in counts.items():
            st.markdown(f'<div style="display:flex; justify-content:space-between; font-size:14px; color:#8b949e; margin-bottom:8px;"><span>{label}:</span><b>{val}</b></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
