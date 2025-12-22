import streamlit as st
import requests, base64, random

# --- 1. 配置 (保持与 app.py 一致) ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"
FILES = {
    "Subject": "subjects.txt", "Action": "actions.txt", 
    "Style": "styles.txt", "Mood": "moods.txt", "Usage": "usage.txt"
}

# --- 2. 工具函数 (从 GitHub 读数据) ---
def get_data(filename):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return [line.strip() for line in base64.b64decode(resp.json()['content']).decode().splitlines() if line.strip()]
    return []

# --- 3. 页面布局 ---
st.title("🎨 创意灵感引擎")

# 同样使用三栏布局
c_left, c_main, c_right = st.columns([1, 4, 2])

# 👉 右栏：仓库预览 (实时查看你的库存)
with c_right:
    st.subheader("📦 素材预览")
    cat_view = st.selectbox("查看维度", list(FILES.keys()))
    # 每次切换都重新读，确保数据最新
    words = get_data(FILES[cat_view])
    with st.container(height=600):
        for w in words:
            st.button(w, key=f"btn_{w}", use_container_width=True)

# 👉 中栏：创意生成核心
with c_main:
    # 1. 上传图片区
    st.markdown("### 📸 参考图反推")
    uploaded_file = st.file_uploader("上传纹身参考图", type=["jpg", "png"])
    if uploaded_file:
        st.image(uploaded_file, width=200)
        st.caption("已识别图片特征：(这里后续接入反推逻辑)")

    st.divider()

    # 2. 随机生成控制
    st.markdown("### 🎲 灵感拼装")
    num_gen = st.slider("一次生成几条创意？", 1, 10, 3)
    
    if st.button("🔥 一键生成创意提示词", type="primary", use_container_width=True):
        st.subheader("💡 生成结果")
        
        # 模拟瀑布流展示
        cols = st.columns(2) 
        for i in range(num_gen):
            # 核心抽样逻辑：从 5 个分类里各摇一个
            sample = []
            for cat, fname in FILES.items():
                all_words = get_data(fname)
                if all_words:
                    sample.append(random.choice(all_words))
            
            # 渲染结果卡片
            with cols[i % 2]:
                with st.container(border=True):
                    final_prompt = " + ".join(sample)
                    st.markdown(f"**方案 {i+1}**")
                    st.code(final_prompt, wrap_lines=True)
                    if st.button(f"选中方案 {i+1}", key=f"sel_{i}"):
                        st.success("已加入待发单列表")

# 👉 左栏：占位
with c_left:
    st.info("💡 提示：点击右侧单词可快速查看详情（开发中）")
