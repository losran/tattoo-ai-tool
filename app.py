import streamlit as st
from openai import OpenAI
import random

# 配置
client = OpenAI(api_key='sk-b18b6a62e0374b3ebab3d961c4806a4c', base_url="https://api.deepseek.com")

st.set_page_config(page_title="Tattoo Studio Pro", layout="wide")

# --- Figma 风格 CSS 注入 ---
st.markdown("""
    <style>
    /* 引入苹果风格字体 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #f5f5f7;
    }

    /* 模拟 Figma 自动布局容器 */
    .flex-container {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        padding: 10px 0;
    }

    /* 苹果风格的胶囊零件 */
    .chip {
        background: white;
        border: 1px solid #d2d2d7;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        color: #1d1d1f;
        font-weight: 500;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    .chip:hover {
        border-color: #0071e3;
        color: #0071e3;
        transform: translateY(-1px);
    }

    /* 侧边栏对齐优化 */
    .stSidebar { background-color: #ffffff; border-right: 1px solid #d2d2d7; }
    
    /* 大标题苹果味优化 */
    h1 { font-weight: 600 !important; letter-spacing: -0.5px !important; color: #1d1d1f !important; }
    h3 { font-size: 16px !important; font-weight: 600 !important; color: #86868b !important; margin-bottom: 5px !important; }

    /* 生成结果卡片 */
    .result-card {
        background: white;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #d2d2d7;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 数据状态初始化
if 'db' not in st.session_state:
    st.session_state.db = {"主体": [], "风格": [], "部位": [], "材质氛围": []}

# --- 侧边栏：输入对齐 ---
with st.sidebar:
    st.markdown("# 录入")
    user_input = st.text_area("输入样板描述", placeholder="在这里粘贴...", height=150)
    if st.button("拆解入库", use_container_width=True, type="primary"):
        if user_input:
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
                    elif "氛围" in k: st.session_state.db["材质氛围"].append(v)
                except: pass
            st.rerun()

# --- 主界面：Figma 自动布局展示 ---
st.title("纹身设计资产库")
st.write("自动化拆解样板零件，实现设计的精准对齐。")
st.markdown("<br>", unsafe_allow_html=True)

# 自动布局展示区
cols = st.columns(4)
sections = [("主体", cols[0]), ("风格", cols[1]), ("部位", cols[2]), ("材质氛围", cols[3])]

for name, col in sections:
    with col:
        st.markdown(f"### {name}")
        # 使用 HTML 实现 Flexbox 自动布局
        items = list(set(st.session_state.db[name]))
        html_content = '<div class="flex-container">'
        for i in items:
            html_content += f'<div class="chip">{i}</div>'
        html_content += '</div>'
        st.markdown(html_content, unsafe_allow_html=True)

st.markdown("<br><hr><br>", unsafe_allow_html=True)

# --- 批量生成区 ---
st.markdown("## 灵感自动生成")
count = st.select_slider("选择生成数量", options=[1, 3, 5, 10], value=5)

if st.button("生成创意组合", type="secondary"):
    db = st.session_state.db
    if all(db.values()):
        # 结果分三列排列，模仿 Figma Grid
        grid = st.columns(3)
        for i in range(count):
            res = {k: random.choice(v) for k, v in db.items()}
            with grid[i % 3]:
                st.markdown(f"""
                <div class="result-card">
                    <span style="color:#0071e3; font-size:12px; font-weight:600;">#方案 {i+1}</span>
                    <h2 style="font-size:20px; margin:10px 0;">{res['风格']} {res['主体']}</h2>
                    <p style="color:#86868b; font-size:14px;">建议位置：{res['部位']}</p>
                    <div style="background:#f5f5f7; padding:12px; border-radius:8px; font-family:monospace; font-size:12px;">
                        {res['主体']}, {res['风格']} tattoo style, {res['材质氛围']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("请先在左侧输入素材进行拆解。")
