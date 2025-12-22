import streamlit as st
import time
from style_manager import apply_pro_style, render_unified_sidebar

# --- 1. 记忆初始化 (新手必看) ---
if "input_val" not in st.session_state:
    st.session_state.input_val = ""  # 存储输入框文字
if "show_warehouse" not in st.session_state:
    st.session_state.show_warehouse = True  # 存储仓库显隐状态

# --- 2. 页面配置与皮肤注入 ---
st.set_page_config(layout="wide", page_title="Alien Mood | 智能入库")
apply_pro_style()

# 统一侧边栏统计
counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}
render_unified_sidebar(counts)

# --- 3. 布局逻辑：受收起开关控制 ---
if st.session_state.show_warehouse:
    col_main, col_right = st.columns([5, 1.8])
else:
    col_main = st.container()

# --- 4. 中间主操作区 ---
with col_main:
    # 顶部工具栏
    c_title, c_toggle = st.columns([5, 1])
    with c_title:
        st.title("⚡ 智能入库")
    with c_toggle:
        toggle_label = "收起仓库 ⮕" if st.session_state.show_warehouse else "⬅ 展开仓库"
        if st.button(toggle_label):
            st.session_state.show_warehouse = not st.session_state.show_warehouse
            st.rerun()

    # 输入框：绑定 session_state
    # 这里的关键是 value=st.session_state.input_val
    user_text = st.text_area(
        "在此输入文案或从右侧点选标签：", 
        value=st.session_state.input_val, 
        height=450,
        key="main_editor_area"
    )
    # 实时保存手打的内容到记忆中
    st.session_state.input_val = user_text

    if st.button("🚀 开始 AI 智能拆解", type="primary", use_container_width=True):
        with st.status("🛸 正在拆解标签结构...", expanded=False):
            st.write("识别主体...")
            time.sleep(0.5)
            st.write("同步数据库...")
            time.sleep(0.5)
        st.toast("拆解完成！")

# --- 5. 右侧仓库区 (仅在展开时显示) ---
if st.session_state.show_warehouse:
    with col_right:
        st.markdown("### 📦 仓库管理")
        cat = st.selectbox("分类", ["Subject", "Style", "Action"], label_visibility="collapsed")
        
        # 模拟单词数据
        words = ["日式 old school", "小圆点", "藤蔓", "郁金香", "雏菊"]
        
        st.write("")
        st.caption("点字导入，点 × 删除")
        
        # 极简标签列表交互
        for idx, w in enumerate(words):
            c_word, c_x = st.columns([5, 1])
            with c_word:
                # 📍 点击文字：直接追加到记忆里并刷新页面
                if st.button(f" {w}", key=f"add_{idx}", use_container_width=True):
                    if st.session_state.input_val:
                        st.session_state.input_val += f" {w}"
                    else:
                        st.session_state.input_val = w
                    st.rerun()
            with c_x:
                # 📍 点击叉号：执行删除逻辑
                if st.button("×", key=f"del_{idx}"):
                    st.toast(f"已从库中清理: {w}")
                    # 这里后续添加真正的 GitHub 删除代码即可
                    time.sleep(0.3)
                    st.rerun()
