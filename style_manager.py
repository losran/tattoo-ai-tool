# style_manager.py
import streamlit as st

def apply_pro_style():
    """统一全站视觉：包含镜像布局、标签自动换行"""
    st.markdown("""
    <style>
        .stApp { background-color: #0f1014; }
        [data-testid="stHeader"] { background: transparent !important; }
        [data-testid="stHeader"] > div:first-child { display: none !important; }

        /* 1. 左侧导航文字放大 */
        [data-testid="stSidebarNav"] ul li div p { font-size: 20px !important; font-weight: 600 !important; }

        /* 2. 📍 右侧固定侧边栏样式 (镜像左侧栏) */
        [data-testid="column"]:nth-child(2) {
            background-color: #16171d !important;
            border-left: 1px solid #262730 !important;
            padding: 40px 15px !important;
            height: 100vh !important;
            position: fixed !important;
            right: 0; top: 0; z-index: 99;
            max-width: 300px !important;
        }

        /* 3. 📍 标签自适应：Hug contents 且文字换行 */
        .stButton > button {
            width: 100% !important;
            height: auto !important;
            padding: 5px 10px !important;
            white-space: normal !important; /* 自动换行 */
            text-align: left !important;
            border: 1px solid #262730 !important;
            background: #1a1b23 !important;
            color: #c9d1d9 !important;
            font-size: 13px !important;
        }
        .stButton > button:hover { border-color: #ff4b4b !important; }

        /* 底部统计文字对齐 */
        .metric-footer { border-top: 1px solid #262730; padding-top: 15px; margin-top: 20px; }
        .metric-item { display: flex; justify-content: space-between; font-size: 13px; color: #8b949e; }
    </style>
    """, unsafe_allow_html=True)

def render_right_warehouse():
    """📍 仓库组件：三个页面共用这一段代码"""
    # 如果没初始化过开关状态，默认开启
    if "is_open" not in st.session_state: st.session_state.is_open = True
    
    # 1. 镜像开关：永远固定在右上角
    # 我们用一个浮动列来放开关
    k1, k2 = st.columns([12, 1])
    with k2:
        icon = "❯" if st.session_state.is_open else "❮ 仓库"
        if st.button(icon, key="global_warehouse_toggle"):
            st.session_state.is_open = not st.session_state.is_open
            st.rerun()

    # 2. 如果是开启状态，渲染仓库内容
    if st.session_state.is_open:
        # 这个 column 会被 CSS 强行推到右侧固定
        _, col_right = st.columns([5, 1.8]) 
        with col_right:
            st.markdown("### 📦 仓库管理")
            cat = st.selectbox("分类", ["Subject", "Style"], label_visibility="collapsed")
            
            # 模拟数据 (以后这里可以对接 GitHub)
            words = ["日式 old school", "小圆点", "非常长的藤蔓刺青纹路", "雏菊"]
            
            st.write("")
            for idx, w in enumerate(words):
                t_col, x_col = st.columns([5, 1.2], gap="small")
                with t_col:
                    if st.button(f" {w}", key=f"comp_add_{w}_{idx}", use_container_width=True):
                        # 点击直接改写 session_state 里的输入值
                        if "input_val" in st.session_state:
                            st.session_state.input_val += f" {w}"
                            st.rerun()
                with x_col:
                    if st.button("✕", key=f"comp_del_{w}_{idx}", use_container_width=True):
                        st.toast(f"已清理: {w}")
                        st.rerun()
