# style_manager.py
import streamlit as st

def apply_global_frame():
    """注入全站锁死的镜像布局 CSS"""
    st.markdown("""
    <style>
        .stApp { background-color: #0f1014; }
        /* 隐藏原生干扰 */
        [data-testid="stHeader"] { background: transparent !important; display: none !important; }

        /* 📍 镜像右边栏：外壳级固定层 */
        .global-right-shell {
            position: fixed;
            right: 0; top: 0;
            width: 320px;
            height: 100vh;
            background-color: #16171d;
            border-left: 1px solid #262730;
            z-index: 999;
            padding: 40px 20px;
            overflow-y: auto;
        }

        /* 📍 中间内容槽：通过 margin 强制对齐左右两堵墙 */
        .main-slot {
            margin-right: 340px;
            padding-bottom: 100px;
        }

        /* 📍 Figma 式标签按钮逻辑 */
        .stButton > button {
            width: 100% !important; height: auto !important;
            white-space: normal !important; text-align: left !important;
            background: #1a1b23 !important; border: 1px solid #262730 !important;
            color: #c9d1d9 !important; padding: 10px !important;
            border-radius: 6px !important;
        }
        .stButton > button:hover { border-color: #ff4b4b !important; }
        
        /* 导航放大至 20px */
        [data-testid="stSidebarNav"] ul li div p { font-size: 20px !important; font-weight: 600 !important; }
    </style>
    """, unsafe_allow_html=True)

def render_global_warehouse():
    """渲染右侧固定仓库外壳"""
    # 初始化全局记忆开关
    if "is_wh_open" not in st.session_state: st.session_state.is_wh_open = True
    
    # 1. 镜像开关按钮（钉在屏幕最右上角）
    with st.container():
        icon = "❯" if st.session_state.is_wh_open else "❮ 仓库"
        # 这是一个绝对定位的按钮模拟
        if st.button(icon, key="global_wh_toggle"):
            st.session_state.is_wh_open = not st.session_state.is_wh_open
            st.rerun()

    # 2. 渲染物理外壳
    if st.session_state.is_wh_open:
        st.markdown('<div class="global-right-shell">', unsafe_allow_html=True)
        st.markdown("### 📦 仓库管理")
        cat = st.selectbox("可视化分类", ["Subject", "Style"], label_visibility="collapsed")
        
        # 这里的单词列表点选后直接改写全局输入记忆
        words = ["日式 old school", "小圆点", "非常长的藤蔓纹路换行测试", "郁金香"]
        for idx, w in enumerate(words):
            c1, c2 = st.columns([5, 1.2])
            with c1:
                if st.button(f" {w}", key=f"wh_add_{idx}", use_container_width=True):
                    st.session_state.input_val += f" {w}"
                    st.rerun()
            with c2:
                if st.button("✕", key=f"wh_del_{idx}"):
                    st.toast(f"已清理: {w}")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
