import streamlit as st

def apply_pro_style():
    st.markdown("""
    <style>
        /* 1. 全局：Apple 黑暗模式底色 */
        .stApp {
            background-color: #000000;
            font-family: -apple-system, "SF Pro Display", "Helvetica Neue", sans-serif;
        }

        /* 2. 隐藏冗余线与页眉 */
        [data-testid="stHeader"] { display: none; }
        footer { visibility: hidden; }

        /* 3. 右侧“仓库”容器：深空灰磨砂感 */
        [data-testid="column"]:nth-child(2) {
            background: rgba(20, 20, 22, 0.8) !important;
            backdrop-filter: blur(30px);
            border-left: 1px solid rgba(255, 255, 255, 0.1) !important;
            padding: 30px 20px !important;
        }

        /* 4. 重点：蓝色呼吸按钮（Apple 风格） */
        .stButton>button {
            background: linear-gradient(135deg, #007AFF 0%, #0051D8 100%) !important;
            border: none !important;
            border-radius: 10px !important;
            color: #ffffff !important;
            font-weight: 500 !important;
            letter-spacing: 0.5px !important;
            padding: 0.6rem 2rem !important;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 122, 255, 0.3) !important;
        }
        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 25px rgba(0, 122, 255, 0.4) !important;
        }

        /* 5. 极简卡片：不再是红坨坨，改为深灰蓝边框 */
        .tag-card {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 10px;
            transition: all 0.2s ease;
        }
        .tag-card:hover {
            background: rgba(0, 122, 255, 0.05);
            border-color: #007AFF;
            transform: scale(1.01);
        }
        
        /* 卡片内文字 */
        .tag-text {
            color: #EBEBF5;
            font-size: 14px;
            font-weight: 400;
        }

        /* 极简删除按钮 */
        .tag-del-btn {
            color: #8E8E93;
            cursor: pointer;
            font-size: 18px;
            transition: color 0.2s;
        }
        .tag-del-btn:hover { color: #FF453A; }

        /* 6. 侧边栏指标：冷色科技感 */
        .metric-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        .metric-label { color: #8E8E93; font-size: 12px; text-transform: uppercase; }
        .metric-value { color: #0A84FF; font-family: 'SF Mono', monospace; font-weight: 600; }

        /* 7. 输入框美化 */
        .stTextArea textarea {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)

def render_unified_sidebar(counts_dict):
    with st.sidebar:
        st.markdown("<h2 style='color:white; letter-spacing:-1px;'>Tattoo AI</h2>", unsafe_allow_html=True)
        st.markdown("<div style='height: 45vh'></div>", unsafe_allow_html=True)
        
        st.markdown('<p style="color:#48484A; font-size:10px; font-weight:600;">SYSTEM TELEMETRY</p>', unsafe_allow_html=True)
        for label, val in counts_dict.items():
            st.markdown(f'''
                <div class="metric-item">
                    <span class="metric-label">{label}</span>
                    <span class="metric-value">{val}</span>
                </div>
            ''', unsafe_allow_html=True)
