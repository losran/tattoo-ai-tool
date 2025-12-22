import streamlit as st

def apply_pro_style():
    """定义全站视觉：包含布局锁定、导航放大、header透明化"""
    st.markdown("""
    <style>
        /* 全局深色底色 */
        .stApp { background-color: #0f1014; color: #c9d1d9; }
        
        /* 📍 修复 Header Bug：保持透明但保留展开按钮 */
        header[data-testid="stHeader"] {
            background: transparent !important;
            color: #c9d1d9 !important;
        }

        /* 📍 导航文字放大：让左侧选项清晰可见 */
        [data-testid="stSidebarNav"] ul li div p {
            font-size: 20px !important; 
            font-weight: 600 !important;
            color: #c9d1d9 !important;
        }

        /* 📍 锁定布局：中间滚动，两侧固定 */
        [data-testid="column"]:nth-child(1) {
            max-height: 90vh !important;
            overflow-y: auto !important;
            padding-right: 20px !important;
        }

        /* 侧边栏底部统计样式：左字右数 */
        .metric-footer {
            border-top: 1px solid #262730;
            padding-top: 20px;
            margin-top: 30px;
        }
        .metric-item {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #8b949e;
            margin-bottom: 8px;
        }
        .metric-val { color: #ffffff; font-weight: bold; }

        /* 统一主按钮：外星情绪红 */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #ff4b4b 0%, #d62f2f 100%) !important;
            border: none !important;
            border-radius: 8px !important;
        }
        
        /* 标签文字按钮样式：极简透明 */
        div[data-testid="stColumn"] button {
            border: 1px solid #262730 !important;
            background: #1a1b23 !important;
            text-align: left !important;
        }
    </style>
    """, unsafe_allow_html=True)

def render_unified_sidebar(counts_dict):
    """渲染侧边栏：导航 + 底部库存统计"""
    with st.sidebar:
        # 留出空间给原生导航
        st.markdown("<br>" * 12, unsafe_allow_html=True)
        
        # 底部常驻统计
        st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
        st.caption("库存统计")
        for label, val in counts_dict.items():
            st.markdown(f'''
                <div class="metric-item">
                    <span>{label}:</span><span class="metric-val">{val}</span>
                </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
