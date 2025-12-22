# style_manager.py
import streamlit as st

def apply_pro_style():
    # 📍 核心修复：取消隐藏 header，否则侧边栏收起后展开按钮会消失
    st.markdown("""
    <style>
        .stApp { background-color: #0f1014; }
        
        /* 1. 放大左侧导航文字 */
        [data-testid="stSidebarNav"] ul li div p {
            font-size: 20px !important; 
            font-weight: 600 !important;
            color: #c9d1d9 !important;
        }

        /* 2. 📍 允许 header 显示，但通过 CSS 抹掉多余的背景，只留按钮 */
        header[data-testid="stHeader"] {
            background: transparent !important;
            color: #c9d1d9 !important;
        }

        /* 3. 中间滚动区：强制锁定高度 */
        .main-scroll-area {
            max-height: 85vh;
            overflow-y: auto;
            padding-right: 15px;
        }

        /* 4. 📍 极简标签：文字 + X */
        .tag-box {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #1a1b23;
            border: 1px solid #262730;
            border-radius: 4px;
            padding: 2px 8px;
            margin-bottom: 5px;
            cursor: pointer;
        }
        .tag-box:hover { border-color: #ff4b4b; }
        .tag-text { color: #c9d1d9; font-size: 14px; flex-grow: 1; }
        .tag-del { color: #4b5563; margin-left: 8px; font-weight: bold; }
        .tag-del:hover { color: #ff4b4b; }

        /* 5. 侧边栏底部统计：去噪音 */
        .metric-footer {
            border-top: 1px solid #262730;
            padding-top: 15px;
            margin-top: 20px;
        }
        .metric-item {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #8b949e;
            margin-bottom: 6px;
        }
    </style>
    """, unsafe_allow_html=True)

def render_unified_sidebar(counts_dict):
    """只保留核心统计，删除没意义的 Alien Mood 文字"""
    with st.sidebar:
        # 直接留空，让原生导航上移
        st.markdown("<br>" * 12, unsafe_allow_html=True)
        
        st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
        st.caption("库存统计")
        for label, val in counts_dict.items():
            st.markdown(f'<div class="metric-item"><span>{label}:</span><b>{val}</b></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
