import streamlit as st
import random, time
from style_manager import apply_global_frame

# --- 1. 状态与外壳初始化 ---
if "input_val" not in st.session_state: st.session_state.input_val = ""
if "is_wh_open" not in st.session_state: st.session_state.is_wh_open = True

st.set_page_config(layout="wide")
apply_global_frame() # 注入物理外壳

# --- 2. 左侧：原生导航与统计 ---
with st.sidebar:
    st.markdown("<br>" * 10, unsafe_allow_html=True)
    st.divider()
    st.caption("库存统计")
    st.markdown("主体: **28**")
    st.markdown("风格: **28**")
    st.markdown("动作: **15**")
    st.markdown("氛围: **12**")

# --- 3. 📍 右侧：平级镜像边栏 (物理外壳) ---
if st.session_state.is_wh_open:
    # 使用 HTML 标签将这块区域强行锁入右侧 fixed 层
    st.markdown('<div class="right-sidebar-shell">', unsafe_allow_html=True)
    
    # 顶部收起开关 (镜像左侧)
    if st.button("❯", key="wh_toggle"):
        st.session_state.is_wh_open = False
        st.rerun()
        
    st.markdown("### 📦 素材仓库")
    cat = st.selectbox("分类", ["Subject", "Style"], label_visibility="collapsed")
    
    # 模拟单词：测试自动换行逻辑
    words = ["old school", "日式传统", "非常长的藤蔓刺青纹路展示换行测试", "浮世绘"]
    for idx, w in enumerate(words):
        c1, c2 = st.columns([5, 1.2], gap="small")
        with c1:
            if st.button(f" {w}", key=f"add_{idx}", use_container_width=True):
                st.session_state.input_val += f" {w}"
                st.rerun()
        with c2:
            if st.button("✕", key=f"del_{idx}"):
                st.toast(f"已清理: {w}")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    # 如果关闭，在右上角留一个极简的“展开”入口
    with st.container():
        if st.button("❮ 仓库", key="expand_btn"):
            st.session_state.is_wh_open = True
            st.rerun()

# --- 4. 中间：业务画布区 ---
# 根据仓库显隐状态切换 CSS 类名
canvas_class = "main-canvas-slot" if st.session_state.is_wh_open else "main-canvas-slot main-canvas-full"
st.markdown(f'<div class="{canvas_class}">', unsafe_allow_html=True)

st.title("🎨 创意引擎")
st.info("💡 点击右侧素材直接导入，点击 🪄 触发随机灵感。")

# 编辑器
st.session_state.input_val = st.text_area(
    "描述创意：", 
    value=st.session_state.input_val, 
    height=450, 
    label_visibility="collapsed"
)

# 功能组
c1, c2 = st.columns(2)
with c1:
    if st.button("🪄 随机灵感组合", use_container_width=True):
        tags = ["机械", "写实", "细线", "重彩"]
        picked = random.choice(tags)
        st.session_state.input_val += f" {picked}"
        st.rerun()
with c2:
    if st.button("🔥 生成创意方案", type="primary", use_container_width=True):
        st.toast("正在调度创意算法...")

st.markdown('</div>', unsafe_allow_html=True)
