import streamlit as st

def apply_pro_style():
    # 这里就是你的“视觉控制面板”
    st.markdown("""
    <style>
        /* 1. 优化文字排版：增加行间距，告别拥挤 */
        html, body, [data-testid="stWidgetLabel"] {
            line-height: 1.8 !important; /* 撑开行高，质感立刻提升 */
            letter-spacing: 0.05em !important; /* 增加字间距 */
        }

        /* 2. 统一卡片样式：磨砂玻璃感 */
        div[data-testid="stButton"] > button {
            border: 1px solid #30363d !important;
            border-radius: 12px !important;
            background-color: #161b22 !important;
            padding: 15px !important;
            transition: 0.3s ease !important;
        }

        /* 3. 统一选中高亮：红色霓虹边框 */
        div[data-testid="stButton"] > button[kind="primary"] {
            border: 2px solid #ff4b4b !important;
            box-shadow: 0 0 15px rgba(255, 75, 75, 0.2) !important;
            background-color: #211d1d !important;
        }

        /* 4. 文本框美化：深色背景 + 呼吸边框 */
        .stTextArea textarea {
            background-color: #0d1117 !important;
            border: 1px solid #30363d !important;
            border-radius: 10px !important;
            padding: 12px !important;
        }

        /* 5. 隐藏 Streamlit 官方自带的杂乱水印 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
