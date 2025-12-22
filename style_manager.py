# style_manager.py
import streamlit as st

def apply_pro_style():
    st.markdown("""
    <style>
        .stApp { background-color: #0f1014; }

        /* 📍 核心：实现 Figma 的 "Hug contents" 效果 */
        .stButton > button {
            width: 100% !important;
            height: auto !important;             /* 高度随内容自适应 */
            min-height: 40px !important;
            padding: 8px 12px !important;
            
            /* 📍 文字自适应换行逻辑 */
            white-space: normal !important;      /* 允许文字自动换行 */
            word-wrap: break-word !important;    /* 强制长单词换行 */
            line-height: 1.4 !important;         /* 增加行间距，防止文字重叠 */
            text-align: left !important;
            
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            
            background: #1a1b23 !important;
            border: 1px solid #262730 !important;
            border-radius: 6px !important;
        }

        /* 悬停变红，保持视觉一致 */
        .stButton > button:hover {
            border-color: #ff4b4b !important;
            background: #211d1d !important;
        }

        /* 修复右侧列的固定宽度，防止比例放大时乱飞 */
        [data-testid="column"]:nth-child(2) {
            max-width: 320px !important; /* 给仓库设个上限，防止它在大屏下散架 */
        }
    </style>
    """, unsafe_allow_html=True)
