import streamlit as st

def apply_pro_style():
    st.markdown("""
    <style>
        /* 1. 基础环境重塑 - 引入 Apple 字体栈 */
        @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;600&display=swap');
        
        .stApp {
            background: radial-gradient(circle at top left, #1c1c1e, #000000);
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* 2. 移除原生冗余组件 */
        [data-testid="stHeader"] { background: rgba(0,0,0,0) !important; }
        [data-testid="stHeader"] > div:first-child { display: none !important; }
        
        /* 3. 右侧“悬浮侧边栏”：磨砂玻璃效果 (Frosted Glass) */
        [data-testid="column"]:nth-child(2) {
            background: rgba(28, 28, 30, 0.7) !important;
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            border-left: 1px solid rgba(255, 255, 255, 0.1) !important;
            padding: 60px 20px !important;
            height: 100vh !important;
            position: fixed !important;
            right: 0; top: 0; z-index: 99;
            box-shadow: -10px 0 30px rgba(0,0,0,0.5);
        }

        /* 4. 📍 极简标签：胶囊型 & 呼吸感边框 */
        .tag-pill {
            display: inline-flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px; /* 彻底圆角化 */
            margin: 4px;
            padding: 4px 12px;
            color: #efeff4;
            font-size: 13px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .tag-pill:hover {
            background: rgba(255, 75, 75, 0.15);
            border-color: #ff3b30; /* Apple Red */
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(255, 59, 48, 0.2);
        }

        /* 5. 侧边栏导航美化 */
        [data-testid="stSidebar"] {
            background-color: #000000 !important;
        }
        [data-testid="stSidebarNav"] ul li div p {
            font-size: 18px !important;
            font-weight: 500 !important;
            letter-spacing: -0.5px;
            color: #ffffff !important;
        }

        /* 6. 底部统计状态卡片 */
        .metric-footer {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            margin-top: 30px;
        }
        .metric-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
            font-family: 'SF Mono', monospace;
        }
        .metric-item span { color: #8e8e93; font-size: 12px; text-transform: uppercase; }
        .metric-item b { 
            color: #ff3b30; 
            font-size: 14px; 
            text-shadow: 0 0 10px rgba(255, 59, 48, 0.3); 
        }

        /* 7. 自定义按钮：红色呼吸灯感 */
        .stButton>button {
            background: linear-gradient(135deg, #ff3b30 0%, #af0917 100%) !important;
            border: none !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 0.6rem 2rem !important;
            font-weight: 600 !important;
            transition: 0.3s !important;
            box-shadow: 0 4px 15px rgba(255, 59, 48, 0.3) !important;
        }
        .stButton>button:hover {
            transform: scale(1.02);
            box-shadow: 0 6px 20px rgba(255, 59, 48, 0.5) !important;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(255, 59, 48, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 59, 48, 0); }
        }
    </style>
    """, unsafe_allow_html=True)

def render_unified_sidebar(counts_dict):
    with st.sidebar:
        # 顶部留白由 padding 处理，这里加一个装饰性的 Logo 占位
        st.markdown("<h2 style='color:white; font-weight:600; letter-spacing:-1px;'>Tattoo AI</h2>", unsafe_allow_html=True)
        st.markdown("<div style='height: 40vh'></div>", unsafe_allow_html=True)
        
        st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
        st.markdown('<p style="color:#8e8e93; font-size:11px; margin-bottom:12px;">SYSTEM STATUS</p>', unsafe_allow_html=True)
        for label, val in counts_dict.items():
            st.markdown(f'''
                <div class="metric-item">
                    <span>{label}</span>
                    <b>{val}</b>
                </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
