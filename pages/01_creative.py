import streamlit as st
import random, time
# 📍 确保你使用的是我上一个回答里重写的 style_manager.py
from style_manager import apply_global_frame, render_global_warehouse

# --- 1. 记忆初始化与皮肤注入 ---
# 确保全站共用同一个输入框记忆
if "input_val" not in st.session_state: st.session_state.input_val = ""

st.set_page_config(layout="wide", page_title="Alien Mood | 创意引擎")
apply_global_frame()       # 刷墙（固定左右侧层级）
render_global_warehouse()  # 立柜（固定右侧资产库）

# --- 2. 左侧侧边栏：常驻统计 (20px 大字) ---
with st.sidebar:
    st.markdown("<br>" * 10, unsafe_allow_html=True)
    st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
    st.caption("库存统计")
    counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}
    for label, val in counts.items():
        st.markdown(f'<div class="metric-item"><span>{label}:</span><b>{val}</b></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 3. 核心业务区：创意引擎工作台 ---
# 📍 关键：包在 main-slot 里，它会自动避开固定的右侧栏
st.markdown('<div class="main-slot">', unsafe_allow_html=True)
st.title("🎨 创意引擎")

# 灵感提示信息
st.info("💡 灵感匮乏？点击右侧仓库素材进行随机组合，或在下方描述你的愿景。")

# 编辑区：值绑定全局记忆，实现右侧仓库点选即入
st.session_state.input_val = st.text_area(
    "创意描述 / 提示词构建：", 
    value=st.session_state.input_val, 
    height=400, 
    label_visibility="collapsed"
)

# 创意页特有的功能按钮组
st.write("")
c1, c2 = st.columns(2)
with c1:
    if st.button("🪄 随机灵感组合", use_container_width=True):
        # 随机从推荐库抓一个词
        random_tags = ["日式", "小圆点", "重彩", "写实", "机械感"]
        picked = random.choice(random_tags)
        st.session_state.input_val += f" {picked}"
        st.toast(f"已注入灵感: {picked}")
        time.sleep(0.5)
        st.rerun()
            
with c2:
    if st.button("🔥 生成创意方案", type="primary", use_container_width=True):
        with st.status("正在进行深度创意联想...") as status:
            time.sleep(1)
            st.write("解析核心关键词...")
            time.sleep(1)
            st.write("匹配视觉 CMF 方案...")
            status.update(label="生成完成！", state="complete")

st.markdown('</div>', unsafe_allow_html=True)
