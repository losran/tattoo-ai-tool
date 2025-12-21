import streamlit as st
from openai import OpenAI
import random

# 配置 DeepSeek
client = OpenAI(api_key='sk-b18b6a62e0374b3ebab3d961c4806a4c', base_url="https://api.deepseek.com")

# 页面配置：适配移动端初始状态
st.set_page_config(page_title="Tattoo Studio", layout="wide", initial_sidebar_state="collapsed")

# --- 极简主义 & 移动端自适应 CSS ---
st.markdown("""
    <style>
    /* 核心背景：兼容深浅模式 */
    :root { --accent-color: #0071e3; --text-main: #1d1d1f; --bg-card: #ffffff; }
    
    /* 自动对齐的胶囊容器 */
    .flex-container {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        padding: 8px 0;
    }

    /* 苹果味零件胶囊：适配深浅模式 */
    .chip {
        background: rgba(128, 128, 128, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 4px 12px;
        border-radius: 100px;
        font-size: 13px;
        color: inherit; /* 随系统文字颜色变化 */
        font-weight: 500;
    }

    /* 移动端对齐优化 */
    @media (max-width: 640px) {
        .stColumns { display: block !important; }
        .stColumn { width: 100% !important; margin-bottom: 20px !important; }
        h1 { font-size: 24px !important; }
    }

    /* 结果卡片美化 */
    .result-card {
        background: rgba(128, 128, 128, 0.05);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.1);
        margin-bottom: 16px;
    }
    
    /* 强制去除按钮的生硬边框 */
    .stButton button { border-radius: 8px !important; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# 数据初始化
if 'db' not in st.session_state:
    st.session_state.db = {"主体": [], "风格": [], "部位": [], "氛围": []}

# --- 侧边栏：移动端收纳 ---
with st.sidebar:
    st.header("📥 素材录入")
    user_input = st.text_area("样板描述", placeholder="粘贴样板文案...", height=120)
    if st.button("开始拆解", use_container_width=True, type="primary"):
        if user_input:
            with st.spinner('解析中...'):
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": "格式:主体:X|风格:X|部位:X|氛围:X"},
                              {"role": "user", "content": user_input}]
                )
                res = response.choices[0].message.content
                for item in res.split("|"):
                    try:
                        k, v = item.split(":")
                        if "主体" in k: st.session_state.db["主体"].append(v)
                        elif "风格" in k: st.session_state.db["风格"].append(v)
                        elif "部位" in k: st.session_state.db["部位"].append(v)
                        elif "氛围" in k: st.session_state.db["氛围"].append(v)
                    except: pass
            st.rerun()

# --- 主界面：响应式布局 ---
st.title("纹身设计资产库")
st.caption("Figma 风格自动布局 · 支持移动端适配")

# 展示区：在PC端分4列，WAP端自动变1列
c1, c2, c3, c4 = st.columns(4)
sections = [("主体", c1), ("风格", c2), ("部位", c3), ("氛围", c4)]

for name, col in sections:
    with col:
        st.write(f"**{name}**")
        items = list(set(st.session_state.db[name]))
        if not items:
            st.caption("待录入...")
        else:
            html = '<div class="flex-container">'
            for i in items:
                html += f'<div class="chip">{i}</div>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

st.markdown("---")

# --- 批量生成：卡片流 ---
st.subheader("🎲 灵感盲盒")
count = st.slider("生成条数", 1, 10, 3)

if st.button("生成创意组合", use_container_width=True):
    db = st.session_state.db
    if all(db.values()):
        # 移动端适配：WAP端显示单列，PC端显示双列
        res_cols = st.columns(1 if st.session_state.get('is_mobile', False) else 2)
        for i in range(count):
            res_s = random.choice(db["主体"])
            res_sty = random.choice(db["风格"])
            res_p = random.choice(db["部位"])
            res_v = random.choice(db["氛围"])
            
            with res_cols[i % len(res_cols)]:
                st.markdown(f"""
                <div class="result-card">
                    <div style="color:var(--accent-color); font-size:12px; font-weight:700; margin-bottom:8px;">CASE {i+1}</div>
                    <div style="font-size:18px; font-weight:600; margin-bottom:4px;">{res_sty}风格{res_s}</div>
                    <div style="font-size:14px; opacity:0.7; margin-bottom:12px;">建议部位：{res_p}</div>
                    <div style="background:rgba(128,128,128,0.1); padding:10px; border-radius:6px; font-size:12px; font-family:monospace;">
                        Prompt: {res_s}, {res_sty} tattoo style, {res_v}, on {res_p}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("库里还没零件，请先录入素材。")
