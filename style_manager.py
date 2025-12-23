def apply_pro_style():
    st.markdown("""
        <style>
        /* 🎨 Figma Dark Mode 精准调色盘 */
        :root {
            --figma-bg: #1E1E1E;        /* 主背景：深炭灰 */
            --figma-sidebar: #2C2C2C;   /* 侧边栏/容器背景 */
            --figma-border: #444444;    /* 描边颜色 */
            --figma-text: #E6E6E6;      /* 主文字：浅灰白 */
            --figma-accent: #18A0FB;    /* Figma 经典蓝（用于点缀） */
            --figma-hover: #3E3E3E;     /* 悬停态 */
        }

        /* 全局背景与文字 */
        .stApp {
            background-color: var(--figma-bg);
            color: var(--figma-text);
        }

        /* 隐藏报错的亮红色，改为 Figma 警告色（深橘红） */
        .stException, .element-container div[data-baseweb="notification"] {
            background-color: #3D2222 !important;
            color: #FFB4B4 !important;
            border: 1px solid #603030 !important;
            border-radius: 6px !important;
        }

        /* 按钮：深灰色容器 + 细描边 */
        div.stButton > button {
            background-color: #2C2C2C !important;
            color: #FFFFFF !important;
            border: 1px solid var(--figma-border) !important;
            border-radius: 6px !important;
            transition: all 0.2s;
        }
        
        div.stButton > button:hover {
            border-color: var(--figma-accent) !important;
            background-color: var(--figma-hover) !important;
        }

        /* 主按钮（激发/润色）：Figma 蓝 */
        div.stButton > button[kind="primary"] {
            background-color: var(--figma-accent) !important;
            border: none !important;
        }

        /* 输入框样式 */
        .stTextArea textarea, .stTextInput input {
            background-color: #2C2C2C !important;
            color: white !important;
            border: 1px solid var(--figma-border) !important;
            border-radius: 4px !important;
        }

        /* 标签/Checkbox 样式：模仿 Figma 图层列表 */
        .stCheckbox {
            padding: 5px;
            border-radius: 4px;
        }
        .stCheckbox:hover {
            background-color: var(--figma-hover);
        }
        </style>
    """, unsafe_allow_html=True)
