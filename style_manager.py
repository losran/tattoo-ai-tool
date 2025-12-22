import streamlit as st

def apply_pro_style():
    """全站视觉装修：放大导航、调暗侧边栏、美化文字"""
    st.markdown("""
    <style>
        /* 1. 整体暗色调 */
        .stApp { background-color: #0f1014; }
        
        /* 2. 📍 重点：放大左侧原生的 app, creative, automation 导航文字 */
        [data-testid="stSidebarNav"] ul li div p {
            font-size: 20px !important; 
            font-weight: 600 !important;
            color: #c9d1d9 !important;
            padding: 8px 0 !important;
        }

        /* 侧边栏整体背景与边框 */
        section[data-testid="stSidebar"] {
            background-color: #16171d !important;
            border-right: 1px solid #262730 !important;
        }

        /* 3. 统计文字的专业排版 (左边字，右边数) */
        .metric-row {
            display: flex;
            justify-content: space-between;
            font-size: 14px;
            color: #8b949e;
            padding: 6px 0;
            border-bottom: 1px solid #262730;
        }
        .metric-val {
            color: #ffffff !important;
            font-weight: bold;
            font-family: monospace;
        }

        /* 隐藏 Streamlit 默认的页脚和多余元素 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def render_unified_sidebar(counts_dict):
    """📍 全站统一侧边栏：放在每个页面的最开头"""
    with st.sidebar:
        # 顶部的品牌 Logo 区域
        st.markdown("### 🛰️ ALIEN MOOD")
        st.caption("Frame...")
        
        # 留出足够的垂直空间，让导航文字之间不拥挤
        st.markdown("<br>" * 8, unsafe_allow_html=True)
        
        # 底部常驻的统计状态
        st.markdown("---")
        st.markdown("**库存统计**")
        
        # 循环显示你传入的统计数据
        for label, val in counts_dict.items():
            st.markdown(f'''
                <div class="metric-row">
                    <span>{label}:</span>
                    <span class="metric-val">{val}</span>
                </div>
            ''', unsafe_allow_html=True)
        
        # 📍 彻底删除登录按钮，不再显示
