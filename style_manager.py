# style_manager.py
import streamlit as st

def apply_pro_style():
    # 1. 视觉装修：放大左侧导航文字，移除冗余
    st.markdown("""
    <style>
        .stApp { background-color: #0f1014; }
        
        /* 📍 放大左侧侧边栏页码导航文字 */
        [data-testid="stSidebarNav"] ul li div p {
            font-size: 18px !important; 
            font-weight: 600 !important;
            color: #c9d1d9 !important;
            padding: 5px 0;
        }
        
        /* 侧边栏整体宽度调整 */
        section[data-testid="stSidebar"] {
            min-width: 200px !important;
        }

        /* 统计文字样式 */
        .sidebar-footer {
            position: fixed;
            bottom: 20px;
            width: 160px;
        }
        .metric-row {
            display: flex;
            justify-content: space-between;
            font-size: 14px;
            color: #8b949e;
            margin-bottom: 8px;
            font-family: monospace;
        }
        .metric-row span:last-child {
            color: #ffffff;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

# 2. 📍 新增：全站统一侧边栏渲染函数
def render_unified_sidebar(counts_dict):
    with st.sidebar:
        # 顶部的 Logo 区域
        st.markdown("### 🛰️ ALIEN MOOD")
        st.caption("Frame...")
        
        # 留出空间给导航
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        
        # 底部统计状态 (不管哪个页面都显示)
        st.divider()
        st.markdown("**统计状态**")
        for label, val in counts_dict.items():
            st.markdown(f'''
                <div class="metric-row">
                    <span>{label}:</span>
                    <span>{val}</span>
                </div>
            ''', unsafe_allow_html=True)
        
        # 彻底删掉登录按钮
