import streamlit as st
import time, random
# 📍 导入你第一步建好的中控盒
from style_manager import apply_pro_style, render_unified_sidebar

# --- 1. 基础配置与视觉初始化 ---
st.set_page_config(layout="wide", page_title="Alien Mood | 智能入库")
apply_pro_style() # 执行全站装修

# 模拟统计数据（实际可根据你的数据库长度计算）
counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}
render_unified_sidebar(counts) # 执行统一侧边栏（导航放大+统计常驻）

# --- 2. 模拟功能逻辑 (保持原样，仅做演示) ---
WAREHOUSE = {
    "Subject": "data/subjects.txt", "Action": "data/actions.txt", 
    "Style": "data/styles.txt", "Mood": "data/moods.txt"
}

def get_github_data(cat):
    # 模拟数据，实际使用你原来的 GitHub 请求逻辑
    return ["日式 old school", "小圆点", "藤蔓", "郁金香纹身", "雏菊"]

# 初始化输入框缓存
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

# --- 3. 页面布局 (5:2 黄金比例) ---
col_main, col_right = st.columns([5, 2.5])

# --- 核心操作区 (中间) ---
with col_main:
    st.title("🎨 智能入库界面")
    st.info("💡 全能拆分助手已上线，助力灵感高效入库！")
    
    # 这里的输入框现在非常宽大，看着就舒服
    user_text = st.text_area(
        "在此输入或粘贴文案：", 
        value=st.session_state.user_input,
        height=400, 
        placeholder="输入内容后，点击下方按钮开始智能拆解...",
        key="main_input_area"
    )
    
    # 更新缓存，确保右侧点击能实时同步
    st.session_state.user_input = user_text

    st.write("")
    if st.button("🚀 开始 AI 智能拆解 (显示进度)", type="primary", use_container_width=True):
        with st.status("🛸 Alien AI 正在解析结构...", expanded=True) as status:
            st.write("识别主体元素...")
            st.progress(30)
            time.sleep(0.4)
            st.write("同步风格仓库...")
            st.progress(70)
            time.sleep(0.4)
            st.progress(100)
            status.update(label="✨ 拆解完成！", state="complete", expanded=False)
        st.success("拆解成功！标签已在下方生成（模拟预览）")

# --- 仓库管理区 (右侧) ---
with col_right:
    st.subheader("📦 仓库管理")
    
    # 类型切换
    cat = st.selectbox("当前查看分类:", list(WAREHOUSE.keys()), label_visibility="collapsed")
    words = get_github_data(cat)
    
    st.divider()
    
    if words:
        st.caption("点击文字导入中间，点击 🗑️ 彻底删除")
        with st.container(height=550):
            for idx, w in enumerate(words):
                # 📍 这里的布局：文字占 4 份，删除键占 1 份
                c_word, c_del = st.columns([4, 1])
                
                with c_word:
                    # 点击文字：直接加入到中间输入框
                    if st.button(f"➕ {w}", key=f"add_{w}_{idx}", use_container_width=True):
                        if st.session_state.user_input:
                            st.session_state.user_input += f" {w}"
                        else:
                            st.session_state.user_input = w
                        st.rerun()
                
                with c_del:
                    # 点击删除：模拟删除逻辑
                    if st.button("🗑️", key=f"del_{w}_{idx}"):
                        st.toast(f"已从云端删除: {w}")
                        time.sleep(0.5)
                        st.rerun()
    else:
        st.info("分类下暂无素材")

    st.divider()
    st.button("批量入库", use_container_width=True)
