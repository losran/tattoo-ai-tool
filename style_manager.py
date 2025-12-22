import streamlit as st

def apply_global_frame():
    """注入全站锁死的镜像布局 CSS"""
    st.markdown("""
    <style>
        /* 1. 全局深色底色与隐藏多余元素 */
        .stApp { background-color: #0f1014; }
        [data-testid="stHeader"] { background: transparent !important; display: none !important; }

        /* 2. 📍 右侧固定外壳：层级与左边栏平级 */
        .global-right-shell {
            position: fixed;
            right: 0; top: 0;
            width: 320px;
            height: 100vh;
            background-color: #16171d;
            border-left: 1px solid #262730;
            z-index: 999;
            padding: 40px 15px;
            overflow-y: auto;
        }

        /* 3. 📍 中间 Slot：强制留出右侧空间，防止内容被遮挡 */
        .main-slot {
            margin-right: 340px;
            padding-bottom: 100px;
        }

        /* 4. 📍 Figma 式 Hug Contents 标签：自动换行 */
        .stButton > button {
            width: 100% !important; height: auto !important;
            white-space: normal !important; /* 强制自动换行 */
            word-break: break-all !important;
            text-align: left !important;
            background: #1a1b23 !important;
            border: 1px solid #262730 !important;
            color: #c9d1d9 !important;
            padding: 8px 12px !important;
            border-radius: 6px !important;
            font-size: 14px !important;
        }
        .stButton > button:hover { border-color: #ff4b4b !important; background: #211d1d !important; }

        /* 5. 导航文字放大至 20px */
        [data-testid="stSidebarNav"] ul li div p { 
            font-size: 20px !important; 
            font-weight: 600 !important; 
            color: #c9d1d9 !important; 
        }

        /* 底部统计状态 */
        .metric-footer { border-top: 1px solid #262730; padding-top: 15px; margin-top: 30px; }
        .metric-item { display: flex; justify-content: space-between; font-size: 13px; color: #8b949e; margin-bottom: 8px; }
    </style>
    """, unsafe_allow_html=True)

def render_global_warehouse():
    """渲染右侧固定仓库外壳"""
    if "is_wh_open" not in st.session_state: st.session_state.is_wh_open = True
    
    # 开关按钮：镜像对齐左侧边栏
    k1, k2 = st.columns([12, 1.2])
    with k2:
        icon = "❯" if st.session_state.is_wh_open else "❮ 仓库"
        if st.button(icon, key="global_wh_toggle"):
            st.session_state.is_wh_open = not st.session_state.is_wh_open
            st.rerun()

    if st.session_state.is_wh_open:
        st.markdown('<div class="global-right-shell">', unsafe_allow_html=True)
        st.markdown("### 📦 仓库管理")
        # 可选分类预览方式
        st.selectbox("分类视图", ["Subject", "Style", "Mood"], label_visibility="collapsed")
        
        # 模拟数据
        words = ["日式 old school", "小圆点", "非常长的藤蔓刺青纹路换行测试", "郁金香"]
        st.write("")
        for idx, w in enumerate(words):
            c1, c2 = st.columns([5, 1.2], gap="small")
            with c1:
                if st.button(f" {w}", key=f"wh_add_{idx}", use_container_width=True):
                    st.session_state.input_val += f" {w}"
                    st.rerun()
            with c2:
                if st.button("✕", key=f"wh_del_{idx}"):
                    st.toast(f"已清理: {w}")
        st.markdown('</div>', unsafe_allow_html=True)
