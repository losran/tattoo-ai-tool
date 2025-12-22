import streamlit as st
import requests, base64, random, time

# --- 1. 样式中控台 (精准还原设计稿质感) ---
def apply_pro_style():
# 每个页面的头部
from style_manager import apply_pro_style, render_unified_sidebar

# 统一装修
apply_pro_style()

# 统一侧边栏：传入你要显示的统计数据即可
counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}
render_unified_sidebar(counts)

# --- 2. 核心功能配置 (保持原逻辑不动) ---
st.set_page_config(layout="wide", page_title="Alien Mood Central")
apply_pro_style() # 注入皮肤

# 模拟数据接口 (请确保你原本的 WAREHOUSE 和 get_github_data 函数在这里可用)
WAREHOUSE = {
    "Subject": "data/subjects.txt", "Action": "data/actions.txt", 
    "Style": "data/styles.txt", "Mood": "data/moods.txt", "Usage": "data/usage.txt"
}

def get_github_data(path):
    # 这里保持你原本的请求逻辑
    return ["日式 old school", "小圆点", "藤蔓", "郁金香纹身", "雏菊"] 

# --- 3. 页面结构还原 (按设计稿重组) ---

# A. 左侧边栏：品牌 Logo + 底部统计
with st.sidebar:
    st.markdown("### 🛰️ ALIEN MOOD")
    st.caption("Frame...")
    st.write("")
    st.caption("智能入库")
    st.caption("生成提示词")
    
    # 占位符，把统计压到底部
    st.markdown("<div style='height: 45vh;'></div>", unsafe_allow_html=True)
    
    st.divider()
    # 还原设计稿的统计文字排版
    st.markdown("**统计状态**")
    db_counts = {"主体": 28, "风格": 28, "动作": 15, "氛围": 12}
    for label, val in db_counts.items():
        st.markdown(f'<div class="sidebar-metric-row"><span>{label}:</span><span class="metric-val">{val}</span></div>', unsafe_allow_html=True)
    
    st.write("")
    st.button("登录", use_container_width=True)

# B. 主操作流 (5:2 比例)
col_main, col_right = st.columns([5, 2.5])

with col_main:
    st.title("智能入库") #
    
    # 模仿设计稿顶部的 Banner
    st.info("💡 全能图片Pro已上线，会员免费用！")
    
    #
    user_input = st.text_area(
        "输入文案", 
        height=400, 
        placeholder="从右边素材库随机提取创意素材...",
        label_visibility="collapsed"
    )
    
    st.write("")
    #
    if st.button("🚀 马上拆解 (AI拆分中...)", type="primary", use_container_width=True):
        st.toast("正在调用 AI 进行标签化处理...")
        # 此处保留你原有的 AI 拆分逻辑代码

# C. 右侧仓库管理
# 📍 定位：app.py 右侧仓库循环部分
with col_right:
    st.subheader("📦 仓库管理")
    
    # 类型切换
    cat = st.selectbox("类型选择:", list(WAREHOUSE.keys()), label_visibility="collapsed")
    words = get_github_data(WAREHOUSE[cat])
    
    st.divider()
    
    if words:
        with st.container(height=500):
            for idx, w in enumerate(words):
                # 📍 核心：一行分两个列，左边点字导入，右边点垃圾桶删除
                c_word, c_del = st.columns([4, 1])
                
                with c_word:
                    # 点击单词：直接追加到中间的输入框里
                    if st.button(f"➕ {w}", key=f"add_{w}_{idx}", use_container_width=True):
                        # 如果框里已经有词了，加个空格再拼上去
                        if st.session_state.manual_editor:
                            st.session_state.manual_editor += f" {w}"
                        else:
                            st.session_state.manual_editor = w
                        st.rerun()
                
                with c_del:
                    # 点击垃圾桶：直接从仓库删除
                    if st.button("🗑️", key=f"del_{w}_{idx}"):
                        remaining = [item for item in words if item != w]
                        save_to_github(WAREHOUSE[cat], remaining)
                        st.toast(f"已删除: {w}") # 冒个泡提醒一下
                        st.rerun()
    else:
        st.info("分类下暂无素材")
            
    #
    st.button("🗑️ 批量清理选中标签", use_container_width=True)


