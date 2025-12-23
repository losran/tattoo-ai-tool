import streamlit as st

def apply_pro_style():
    st.markdown("""
    <style>
        /* 1. 基础环境：纯黑底色 + SF Pro 字体栈 */
        .stApp {
            background-color: #000000;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
        }

        /* 隐藏无用组件 */
        [data-testid="stHeader"] { display: none; }
        footer { visibility: hidden; }

        /* 2. 右侧仓库容器：极简细边分割 */
        [data-testid="column"]:nth-child(2) {
            background: rgba(10, 10, 10, 0.4) !important;
            backdrop-filter: blur(20px);
            border-left: 0.5px solid rgba(255, 255, 255, 0.1) !important;
            padding: 30px 15px !important;
        }

        /* 3. 核心：仓库标签 - 淡淡的轮廓线风格 */
        .tag-card {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: transparent; /* 移除背景填充 */
            border: 0.8px solid rgba(255, 255, 255, 0.15); /* 淡淡的轮廓 */
            border-radius: 8px;
            padding: 10px 14px;
            margin-bottom: 8px;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        /* 鼠标指上去时的交互：轮廓变亮，背景微弱变蓝 */
        .tag-card:hover {
            border-color: #007AFF; /* 苹果标准蓝 */
            background: rgba(0, 122, 255, 0.05);
            box-shadow: 0 0 10px rgba(0, 122, 255, 0.1);
        }
        
        /* 标签文字：更细、更优雅 */
        .tag-text {
            color: rgba(255, 255, 255, 0.85);
            font-size: 13.5px;
            font-weight: 300;
            letter-spacing: 0.3px;
        }

        /* 删除按钮：平时隐藏，鼠标移入卡片时显现 */
        .tag-del-btn {
            color: rgba(255, 255, 255, 0.3);
            cursor: pointer;
            font-size: 16px;
            font-weight: 200;
            transition: 0.2s;
        }
        .tag-card:hover .tag-del-btn {
            color: #FF3B30; /* 只有要删除时才显示红色警告感 */
        }

        /* 4. 侧边栏指标统计：数字高亮，文字暗淡 */
        .metric-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 0.5px solid rgba(255, 255, 255, 0.08);
        }
        .metric-label { color: #636366; font-size: 11px; font-weight: 500; }
        .metric-value { color: #0A84FF; font-family: 'SF Mono', monospace; font-size: 13px; }

        /* 5. 蓝色主按钮：保持高级渐变感但减小阴影 */
        .stButton>button {
            background: linear-gradient(180deg, #007AFF 0%, #0063E2 100%) !important;
            border: none !important;
            border-radius: 8px !important;
            color: white !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            padding: 0.5rem 1.5rem !important;
            box-shadow: 0 2px 8px rgba(0, 122, 255, 0.2) !important;
        }

        /* 6. 输入框：同步轮廓线风格 */
        .stTextArea textarea {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 0.8px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
            color: #ffffff !important;
            font-size: 14px !important;
        }
        .stTextArea textarea:focus {
            border-color: #007AFF !important;
            box-shadow: 0 0 0 1px #007AFF !important;
        }
    </style>
    """, unsafe_allow_html=True)
