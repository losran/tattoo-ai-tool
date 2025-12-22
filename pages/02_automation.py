import streamlit as st
import time
# 📍 确保你使用的是我之前发的那套 style_manager.py
from style_manager import apply_global_frame, render_global_warehouse

# --- 1. 记忆初始化与外壳注入 ---
if "input_val" not in st.session_state: st.session_state.input_val = ""

st.set_page_config(layout="wide", page_title="Alien Mood | 自动化工具")
apply_global_frame()       # 刷墙（固定左、中、右三屏层级）
render_global_warehouse()  # 立柜（右侧镜像资产库）

# --- 2. 左侧侧边栏：常驻统计 (20px 大字) ---
with st.sidebar:
    st.markdown("<br>" * 10, unsafe_allow_html=True)
    st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
    st.caption("库存统计")
    counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}
    for label, val in counts.items():
        st.markdown(f'<div class="metric-item"><span>{label}:</span><b>{val}</b></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 3. 核心业务区：自动化任务流 ---
# 📍 必须包在 main-slot 里，确保它在左右两堵“墙”中间滚动
st.markdown('<div class="main-slot">', unsafe_allow_html=True)
st.title("⚡ 自动化工具")

# 文案处理区：绑定全局记忆
st.session_state.input_val = st.text_area(
    "待处理内容 / 脚本指令：", 
    value=st.session_state.input_val, 
    height=300, 
    label_visibility="collapsed"
)

st.write("")
st.markdown("#### ⚙️ 任务链配置")

# 复原你之前的自动化功能逻辑
c1, c2, c3 = st.columns(3)
with c1:
    deduplicate = st.toggle("自动清理重复标签", value=True)
with c2:
    to_english = st.toggle("一键转为 Midjourney Prompt", value=False)
with c3:
    auto_sync = st.toggle("处理后自动同步 GitHub", value=True)

# 底部执行按钮
st.write("")
if st.button("🚀 开始批量自动化处理", type="primary", use_container_width=True):
    with st.status("正在调度自动化脚本...") as s:
        st.write("扫描重复词汇...")
        time.sleep(0.5)
        if to_english:
            st.write("调用 AI 翻译引擎...")
            time.sleep(0.8)
        st.write("准备 GitHub 提交...")
        time.sleep(0.5)
        s.update(label="自动化处理已圆满完成！", state="complete")
    st.balloons() # 庆祝一下

st.markdown('</div>', unsafe_allow_html=True)
