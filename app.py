import streamlit as st
import requests, base64, random, time

# --- 1. 样式中控台 (精准还原设计稿质感) ---
def apply_pro_style():
    st.markdown("""
    <style>
        /* 全局深色底色 */
        .stApp { background-color: #0f1014; color: #c9d1d9; }
        
        /* 左侧边栏：窄边黑化，适配设计稿 */
        section[data-testid="stSidebar"] {
            background-color: #16171d !important;
            border-right: 1px solid #262730 !important;
            min-width: 160px !important;
        }
        
        /* 侧边栏底部统计：简洁文字对齐 */
        .sidebar-metric-container {
            margin-top: 20px;
            padding: 10px 0;
        }
        .sidebar-metric-row {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #8b949e;
            margin-bottom: 8px;
        }
        .metric-val { color: #ffffff; font-weight: 600; }

        /* 中间输入框：磨砂感，无缝融入背景 */
        .stTextArea textarea {
            background-color: #1a1b23 !important;
            border: 1px solid #262730 !important;
            border-radius: 10px !important;
            padding: 15px !important;
            color: #d1d5db !important;
        }

        /* 右侧仓库管理区：卡片化分层 */
        div[data-testid="stVerticalBlock"] > div[style*="border"] {
            background-color: #16171d !important;
            border: 1px solid #262730 !important;
            border-radius: 12px !important;
            padding: 15px !important;
        }

        /* 统一红色主按钮：外星情绪品牌色 */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #ff4b4b 0%, #d62f2f 100%) !important;
            border: none !important;
            border-radius: 8px !important;
            height: 48px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 15px rgba(255, 75, 75, 0.2) !important;
        }
        
        /* 隐藏无用组件 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

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
with col_right:
    st.subheader("📦 仓库管理")
    
    # 模拟设计稿顶部的过滤与选择
    r_c1, r_c2 = st.columns([1, 2])
    with r_c1:
        st.checkbox("仅收藏")
    with r_c2:
        view_mode = st.selectbox("类型:", list(WAREHOUSE.keys()), label_visibility="collapsed")
    
    # 仓库列表
    words = get_github_data(WAREHOUSE.get(view_mode, "Subject"))
    
    with st.container(height=550, border=True):
        if words:
            st.caption(f"生成的提示词标签将在下面展示 (共 {len(words)} 个)")
            for w in words:
                # 选中的提示词高亮
                st.checkbox(f" {w}", key=f"warehouse_{w}")
        else:
            st.info("暂无素材数据")
            
    #
    st.button("🗑️ 批量清理选中标签", use_container_width=True)
