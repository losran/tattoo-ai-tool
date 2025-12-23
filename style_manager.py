import streamlit as st

def apply_pro_style():
    # 🎨 这里的 CSS 只管颜色和 UI 皮肤，不碰你一行业务逻辑
    st.markdown("""
        <style>
        /* 1. 强制 Figma 深色底色 */
        .stApp {
            background-color: #1E1E1E !important;
            color: #E6E6E6 !important;
        }

        /* 2. 把那该死的红色报错框变灰 (黑白灰语义) */
        .stException, div[data-baseweb="notification"] {
            background-color: #2C2C2C !important;
            color: #AAAAAA !important;
            border: 1px solid #444444 !important;
            border-radius: 4px !important;
        }

        /* 3. 侧边栏改为 Figma 侧栏深灰 */
        section[data-testid="stSidebar"] {
            background-color: #2C2C2C !important;
            border-right: 1px solid #444444 !important;
        }

        /* 4. 按钮统一：黑底、白字、细灰边 */
        div.stButton > button {
            background-color: #2C2C2C !important;
            color: #FFFFFF !important;
            border: 1px solid #444444 !important;
            border-radius: 4px !important;
        }
        
        /* 5. 悬停效果：深灰变中灰 */
        div.stButton > button:hover {
            border-color: #888888 !important;
            background-color: #3E3E3E !important;
        }

        /* 6. 输入框和下拉框：Figma 风格输入区 */
        .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
            background-color: #2C2C2C !important;
            color: white !important;
            border: 1px solid #444444 !important;
        }

        /* 7. 进度条和滑块改为深灰色系 */
        .stSlider div[data-baseweb="slider"] {
            background-color: #333333 !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_unified_sidebar(counts):
    # 这里保持你原本的侧边栏统计逻辑，只管显示，不准动数据
    with st.sidebar:
        st.markdown("### 📊 仓库统计")
        for k, v in counts.items():
            st.write(f"{k}: **{v}**")
