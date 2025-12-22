import streamlit as st

def apply_global_frame():
    """强制构建三栏平级物理架构：左导航、中画布、右资产"""
    st.markdown("""
    <style>
        .stApp { background-color: #0f1014; }
        [data-testid="stHeader"] { display: none !important; }

        /* 📍 右侧镜像边栏：物理层级与左侧一致，钉死在最右 */
        .right-sidebar-shell {
            position: fixed;
            right: 0; top: 0;
            width: 320px;
            height: 100vh;
            background-color: #16171d;
            border-left: 1px solid #262730;
            z-index: 9999;
            padding: 40px 15px;
            overflow-y: auto;
        }

        /* 📍 中间画布：通过 margin 避开两边的墙 */
        .main-canvas-slot {
            margin-right: 340px; 
            margin-left: 0;
            padding: 20px;
            max-height: 98vh;
            overflow-y: auto;
        }
        
        /* 📍 Figma 级标签：Hug contents & 自动换行 */
        .stButton > button {
            width: 100% !important;
            height: auto !important;
            white-space: normal !important;
            word-break: break-all !important;
            text-align: left !important;
            padding: 10px 12px !important;
            background: #1a1b23 !important;
            border: 1px solid #262730 !important;
            border-radius: 6px !important;
            color: #c9d1d9 !important;
        }
        .stButton > button:hover { border-color: #ff4b4b !important; }

        /* 左侧导航 20px 大字 */
        [data-testid="stSidebarNav"] ul li div p { font-size: 20px !important; font-weight: 600 !important; }
        .metric-footer { border-top: 1px solid #262730; padding-top: 15px; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

def render_global_sidebar():
    """左侧常驻统计"""
    with st.sidebar:
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
        st.caption("库存统计")
        counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}
        for label, val in counts.items():
            st.markdown(f'<div style="display:flex; justify-content:space-between; font-size:13px; color:#8b949e; margin-bottom:6px;"><span>{label}:</span><b>{val}</b></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def render_right_shell(content_func):
    """右侧仓库外壳渲染容器"""
    if "is_wh_open" not in st.session_state: st.session_state.is_wh_open = True
    
    # 镜像开关按钮
    k1, k2 = st.columns([12, 1.2])
    with k2:
        icon = "❯" if st.session_state.is_wh_open else "❮ 仓库"
        if st.button(icon, key="global_toggle"):
            st.session_state.is_wh_open = not st.session_state.is_wh_open
            st.rerun()
            
    if st.session_state.is_wh_open:
        st.markdown('<div class="right-sidebar-shell">', unsafe_allow_html=True)
        content_func()
        st.markdown('</div>', unsafe_allow_html=True)
