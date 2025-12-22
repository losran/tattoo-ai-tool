import streamlit as st
import random, time
# 📍 这里的 style_manager 必须用我上一个回答里的最新版
from style_manager import apply_pro_style

# --- 1. 核心状态记忆与皮肤注入 ---
if "input_val" not in st.session_state: st.session_state.input_val = ""
if "is_open" not in st.session_state: st.session_state.is_open = True

st.set_page_config(layout="wide", page_title="Alien Mood | 创意引擎")
apply_pro_style() # 注入全站皮肤

# 模拟统计数据 (与首页保持同步)
counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}

# --- 2. 左侧侧边栏：大字导航 + 常驻统计 ---
with st.sidebar:
    st.markdown("<br>" * 10, unsafe_allow_html=True)
    st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
    st.caption("库存统计")
    for label, val in counts.items():
        st.markdown(f'<div class="metric-item"><span>{label}:</span><span class="metric-val">{val}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 3. 右上角开关：镜像左侧闭合逻辑 ---
btn_col1, btn_col2 = st.columns([12, 1])
with btn_col2:
    icon = "❯" if st.session_state.is_open else "❮ 仓库"
    if st.button(icon, key="creative_sidebar_toggle"):
        st.session_state.is_open = not st.session_state.is_open
        st.rerun()

# --- 4. 核心布局逻辑 ---
if st.session_state.is_open:
    col_main, col_right = st.columns([5, 1.8])
else:
    col_main = st.container()

# --- 5. 中间主操作区：创意灵感工作台 ---
with col_main:
    st.title("🎨 创意引擎")
    st.info("💡 灵感匮乏？点击右侧仓库素材进行随机组合，或在下方描述你的愿景。")
    
    # 编辑区：绑定全局记忆，实现点击导入
    user_text = st.text_area("创意描述 / 提示词构建：", value=st.session_state.input_val, height=400, label_visibility="collapsed")
    st.session_state.input_val = user_text

    # 创意页特有的功能按钮组
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🪄 随机灵感组合", use_container_width=True):
            # 模拟从仓库随机抽词逻辑
            random_tags = ["日式", "小圆点", "重彩", "写实"]
            picked = random.choice(random_tags)
            st.session_state.input_val += f" {picked}"
            st.toast(f"已为您注入灵感: {picked}")
            time.sleep(0.5)
            st.rerun()
            
    with c2:
        if st.button("🔥 生成创意方案", type="primary", use_container_width=True):
            with st.status("正在通过核心算法生成创意组合...") as status:
                time.sleep(1)
                st.write("识别核心词根...")
                time.sleep(1)
                st.write("匹配视觉风格...")
                status.update(label="生成完成！", state="complete")

# --- 6. 右侧固定仓库 (镜像对齐) ---
if st.session_state.is_open:
    with col_right:
        st.markdown("### 📦 素材仓库")
        # 保持极简下拉与标签点选逻辑
        cat = st.selectbox("分类选择", ["Subject", "Style", "Mood"], label_visibility="collapsed")
        
        # 模拟数据
        words = ["old school", "日式传统", "浮世绘", "极简细线", "几何图形"]
        
        st.write("")
        st.caption("点击文字导入，点击 ✕ 清理")
        
        for idx, w in enumerate(words):
            # 组合标签：文字和叉号视觉上一体化
            t_col, x_col = st.columns([5, 1.2], gap="small")
            with t_col:
                if st.button(f" {w}", key=f"cr_add_{idx}", use_container_width=True):
                    st.session_state.input_val += f" {w}"
                    st.rerun()
            with x_col:
                if st.button("✕", key=f"cr_del_{idx}", use_container_width=True):
                    st.toast(f"已清理素材: {w}")
                    st.rerun()
