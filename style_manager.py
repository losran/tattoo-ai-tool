# style_manager.py
import streamlit as st

def apply_pro_style():
    st.markdown("""
    <style>
        /* 1. 🎨 Figma 质感深色：深炭灰背景，告别纯黑 */
        .stApp { 
            background-color: #121212; 
            color: #E0E0E0; 
        }
        [data-testid="stHeader"] { background: transparent !important; }

        /* 2. 🚫 杀掉报错红：改为克制的“深红褐色”背景 */
        .stException, div[data-baseweb="notification"], .stAlert {
            background-color: #2D1B1B !important;
            color: #FFB4B4 !important;
            border: 1px solid #4D2D2D !important;
            border-radius: 8px !important;
        }

        /* 3. 📍 右侧面板：带有高级磨砂感的深灰 */
        [data-testid="column"]:nth-child(2) {
            background-color: #1E1E1E !important;
            border-left: 1px solid #333333 !important;
            padding: 40px 15px !important;
            height: 100vh !important;
            position: fixed !important;
            right: 0; top: 0; z-index: 99;
            box-shadow: -4px 0 15px rgba(0,0,0,0.3);
        }

        /* 4. 🏷️ 极简标签：深色背景 + 极细边框光 */
        .tag-pill {
            display: flex;
            align-items: center;
            background: #252525;
            border: 1px solid #3A3A3A;
            border-radius: 6px;
            margin-bottom: 6px;
            padding: 4px 12px;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            color: #CCCCCC;
            font-size: 14px;
        }
        /* 悬停不再变红，而是边框亮起 */
        .tag-pill:hover { 
            border-color: #18A0FB; 
            background: #2A2A2A; 
            color: #FFFFFF;
        }

        /* 5. 🔘 按钮：Figma 风格的克制灰 */
        div.stButton > button {
            background-color: #2C2C2C !important;
            color: #EEEEEE !important;
            border: 1px solid #444444 !important;
            border-radius: 6px !important;
            transition: all 0.2s !important;
        }
        div.stButton > button:hover { 
            border-color: #666666 !important; 
            background-color: #333333 !important; 
        }
        
        /* ⚡ 主按钮：保持唯一的品牌蓝 */
        div.stButton > button[kind="primary"] {
            background-color: #18A0FB !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(24, 160, 251, 0.2) !important;
        }

        /* 6. ✍️ 输入框：深沉的嵌入感 */
        .stTextArea textarea {
            background-color: #1E1E1E !important;
            color: #FFFFFF !important;
            border: 1px solid #333333 !important;
            border-radius: 8px !important;
        }
        .stTextArea textarea:focus {
            border-color: #18A0FB !important;
        }

        /* 📊 底部统计：低调暗灰 */
        .metric-footer { border-top: 1px solid #333333; padding-top: 15px; margin-top: 20px; }
        .metric-item { display: flex; justify-content: space-between; font-size: 13px; color: #666666; }
        .metric-item b { color: #BBBBBB; }
    </style>
    """, unsafe_allow_html=True)
