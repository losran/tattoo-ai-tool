import streamlit as st
from openai import OpenAI
import random

# 配置 DeepSeek
client = OpenAI(api_key='sk-b18b6a62e0374b3ebab3d961c4806a4c', base_url="https://api.deepseek.com")

# 强制适配移动端 WAP
st.set_page_config(page_title="Tattoo Studio", layout="wide", initial_sidebar_state="collapsed")

# --- 自适应配色 CSS (解决白底白字) ---
st.markdown("""
    <style>
    /* 核心：无论深浅模式，文字都要有底色 */
    .asset-tag {
        display: inline-block;
        background: rgba(0, 113, 227, 0.1);
        color: #0071e3 !important;
        border: 1px solid rgba(0, 113, 227, 0.2);
        padding: 4px 12px;
        border-radius: 100px;
        font-size: 13px;
        font-weight: 500;
        margin: 3px;
    }
    
    /* 结果卡片对齐 */
    .res-card {
        background: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.1);
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
    }

    /* 移动端标题适配 */
    @media (max-width: 640px) {
        .main-title { font-size: 1.5rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

# 数据初始化
if 'db' not in st.session_state:
    st.session_state.db = {"主体": [], "风格": [], "部位": [], "氛围": []}

# --- 侧边栏：移动端录入 ---
with st.sidebar:
    st.header("📥 素材录入")
    user_input = st.text_area("样板描述", placeholder="粘贴描述...", height=150)
    # 增加 loading 状态提示
    if st.button("开始拆解并入库", use_container_width=True, type="primary"):
        if user_input:
            # 增加 try 模块防止卡死
            try:
                with st.spinner('正在连接云端 AI...'):
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "你是一个拆解专家。按 格式: 主体:X|风格:X|部位:X|氛围:X 拆解。不要废话。"},
                                  {"role": "user", "content": user_input}],
                        timeout=15 # 设置超时，防止一直转圈
                    )
                    res_text = response.choices[0].message.content
                    # 自动分类逻辑
                    for item in res_text.split("|"):
                        if ":" in item:
                            k, v = item.split(":", 1)
                            if "主体" in k: st.session_state.db["主体"].append(v.strip())
                            elif "风格" in k: st.session_state.db["风格"].append(v.strip())
                            elif "部位" in k: st.session_state.db["部位"].append(v.strip())
                            elif "氛围" in k: st.session_state.db["氛围"].append(v.strip())
                    st.success("分类成功！")
            except Exception as e:
                st.error(f"连接超时或失败: {e}")
            st.rerun()

# --- 主界面：Figma 自动布局 ---
st.markdown("<h1 class='main-title'>🎨 纹身设计资产看板</h1>", unsafe_allow_html=True)

# 自动布局：PC 4列，WAP 自动折行
sections = ["主体", "风格", "部位", "氛围"]
cols = st.columns(4)

for i, name in enumerate(sections):
    with cols[i]:
        st.markdown(f"### {name}")
        items = list(set(st.session_state.db[name]))
        if items:
            # 使用 Flexbox 自动布局对齐
            html_tags = "".join([f'<span class="asset-tag">{x}</span>' for x in items])
            st.markdown(f'<div style="display:flex; flex-wrap:wrap;">{html_tags}</div>', unsafe_allow_html=True)
        else:
            st.caption("暂无零件")

st.markdown("---")

# --- 生成区 ---
st.subheader("🎲 灵感批量生成")
count = st.slider("生成数量", 1, 10, 3)

if st.button("生成创意组合", use_container_width=True):
    db = st.session_state.db
    if all(len(v) > 0 for v in db.values()):
        st.balloons()
        res_cols = st.columns(2)
        for i in range(count):
            s, sty, p, v = [random.choice(db[k]) for k in sections]
            with res_cols[i % 2]:
                st.markdown(f"""
                <div class="res-card">
                    <b style="color:#0071e3;">方案 {i+1}</b>
                    <div style="font-size:18px; margin:8px 0;">{sty} x {s}</div>
                    <div style="font-size:14px; opacity:0.8;">建议位置: {p} | 质感: {v}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("库里零件不足，请先在侧边栏拆解样板！")
