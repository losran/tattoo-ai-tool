# style_manager.py
import streamlit as st

def apply_pro_style():
    st.markdown("""
    <style>
        /* 1. 全局背景与布局 */
        .stApp { background-color: #0f1014; }
        
        /* 2. 📍 右侧伪装侧边栏：让它和左边长得一模一样 */
        [data-testid="column"]:nth-child(2) {
            background-color: #16171d !important;
            border-left: 1px solid #262730 !important;
            padding: 20px !important;
            height: 100vh !important;
            position: fixed !important;
            right: 0;
            top: 0;
        }

        /* 3. 📍 极简组合标签：文字和叉号在同一个框里 */
        .stButton > button {
            border: 1px solid #262730 !important;
            background: #1a1b23 !important;
            border-radius: 4px !important;
            color: #c9d1d9 !important;
            transition: 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100% !important;
            padding: 4px 10px !important;
            text-align: left !important;
        }
        .stButton > button:hover {
            border-color: #ff4b4b !important;
            color: #ffffff !important;
        }

        /* 4. 让左侧收起后的按钮保持可见 */
        header[data-testid="stHeader"] { background: transparent !important; }

        /* 5. 底部统计状态样式 */
        .metric-footer { border-top: 1px solid #262730; padding-top: 15px; margin-top: 20px; }
        .metric-item { display: flex; justify-content: space-between; font-size: 13px; color: #8b949e; margin-bottom: 6px; }
    </style>
    """, unsafe_allow_html=True)

def render_unified_sidebar(counts_dict):
    """常驻侧边栏：砍掉没意义的文字，只留统计"""
    with st.sidebar:
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
        st.caption("库存统计")
        for label, val in counts_dict.items():
            st.markdown(f'<div class="metric-item"><span>{label}:</span><b>{val}</b></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
