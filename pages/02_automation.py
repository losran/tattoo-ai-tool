import streamlit as st
import time
# 📍 确保你已经把 style_manager.py 覆盖成了我刚才发的那个版本
from style_manager import apply_pro_style

# --- 1. 记忆初始化与皮肤注入 ---
if "input_val" not in st.session_state: st.session_state.input_val = ""
if "is_open" not in st.session_state: st.session_state.is_open = True

st.set_page_config(layout="wide", page_title="Alien Mood | 自动化工具")
apply_pro_style() # 注入全站皮肤

# --- 2. 侧边栏：常驻统计状态 (20px 大字导航) ---
with st.sidebar:
    st.markdown("<br>" * 10, unsafe_allow_html=True)
    st.markdown('<div class="metric-footer">', unsafe_allow_html=True)
    st.caption("库存统计")
    counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}
    for label, val in counts.items():
        st.markdown(f'<div class="metric-item"><span>{label}:</span><b>{val}</b></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 3. 右上角开关：镜像闭合逻辑 ---
btn_col1, btn_col2 = st.columns([12, 1])
with btn_col2:
    icon = "❯" if st.session_state.is_open else "❮ 仓库"
    if st.button(icon, key="auto_sidebar_toggle"):
        st.session_state.is_open = not st.session_state.is_open
        st.rerun()

# --- 4. 核心布局逻辑 ---
if st.session_state.is_open:
    col_main, col_right = st.columns([5, 1.8])
else:
    col_main = st.container()

# --- 5. 中间主操作区：自动化任务流 ---
with col_main:
    st.title("⚡ 自动化工具")
    
    # 输入区：绑定全局记忆，支持仓库点选导入
    st.session_state.input_val = st.text_area(
        "自动化处理文案 / 脚本输入：", 
        value=st.session_state.input_val, 
        height=300,
        label_visibility="collapsed"
    )

    st.write("")
    st.markdown("#### ⚙️ 任务配置")
    
    # 复原你之前的自动化功能开关
    c1, c2, c3 = st.columns(3)
    with c1:
        deduplicate = st.toggle("自动去重标签", value=True)
    with c2:
        to_english = st.toggle("自动翻译为 Prompt", value=False)
    with c3:
        auto_sync = st.toggle("执行后同步云端", value=True)

    # 执行按钮
    if st.button("🚀 执行批量自动化处理", type="primary", use_container_width=True):
        with st.status("正在运行脚本任务流...") as s:
            st.write("清理重复项...")
            time.sleep(0.6)
            if to_english:
                st.write("调用翻译接口...")
                time.sleep(0.8)
            st.write("同步 GitHub 仓库状态...")
            time.sleep(0.5)
            s.update(label="全部自动化任务已完成！", state="complete")
        st.balloons()

# --- 6. 右侧固定仓库 (全站统一组件) ---
if st.session_state.is_open:
    with col_right:
        st.markdown("### 📦 资产仓库")
        cat = st.selectbox("分类查看", ["Subject", "Action", "Style"], label_visibility="collapsed")
        
        # 模拟数据
        words = ["机械臂", "赛博朋克", "霓虹灯", "雨夜", "24x24点阵"]
        
        st.write("")
        for idx, w in enumerate(words):
            # 文字和叉号在一个框里，左点加，右点删
            t_col, x_col = st.columns([5, 1.2], gap="small")
            with t_col:
                if st.button(f" {w}", key=f"auto_add_{idx}", use_container_width=True):
                    st.session_state.input_val += f" {w}"
                    st.rerun()
            with x_col:
                if st.button("✕", key=f"auto_del_{idx}", use_container_width=True):
                    st.toast(f"已从库中移除: {w}")
                    st.rerun()
