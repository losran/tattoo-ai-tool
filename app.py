import streamlit as st
from openai import OpenAI
import random
import os

# --- 配置区 ---
# 请重新填入你的 KEY
client = OpenAI(api_key='sk-b18b6a62e0374b3ebab3d961c4806a4c', base_url="https://api.deepseek.com")

st.set_page_config(page_title="纹身贴创意控制台 Pro", layout="wide")

# 强制使用 UTF-8 读取的函数
def load_words(file_name):
    path = f"data/{file_name}.txt"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return [l.strip() for l in f.readlines() if l.strip()]
    return []

def save_word(file_name, word):
    path = f"data/{file_name}.txt"
    existing = load_words(file_name)
    if word not in existing and word:
        with open(path, "a", encoding="utf-8") as f:
            f.write(word + "\n")

# --- 侧边栏：录入 ---
st.sidebar.header("📥 样板素材导入")
user_input = st.sidebar.text_area("输入中文样板描述：", height=150)
if st.sidebar.button("✨ 自动化拆解入库"):
    if user_input:
        with st.spinner('AI 正在拆分零件...'):
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": "你是一个纹身专家，请按 格式: 主体:XX|风格:XX|部位:XX|氛围:XX 拆解描述。"},
                          {"role": "user", "content": user_input}]
            )
            res = response.choices[0].message.content
            for item in res.split("|"):
                k, v = item.split(":")
                if "主体" in k: save_word("subjects", v)
                elif "风格" in k: save_word("styles", v)
                elif "部位" in k: save_word("placements", v)
                elif "氛围" in k: save_word("vibes", v)
        st.sidebar.success("入库成功！页面已刷新。")

# --- 主界面：文字可视化 ---
st.title("💎 纹身贴文字资产看板")
st.markdown("---")

c1, c2, c3, c4 = st.columns(4)
boxes = [("subjects", "🐲 主体库", c1), ("styles", "🎨 风格库", c2), 
         ("placements", "📍 部位库", c3), ("vibes", "✨ 材质/氛围库", c4)]

for file, label, col in boxes:
    with col:
        st.subheader(label)
        words = load_words(file)
        for w in words:
            st.markdown(f"""<div style="background-color: #f0f2f6; padding: 10px; border-radius: 10px; margin-bottom: 5px; border-left: 5px solid #ff4b4b;">{w}</div>""", unsafe_allow_html=True)

# --- 底部：批量抽卡 ---
st.markdown("---")
st.header("🎲 创意盲盒批量生成")
count = st.slider("想要一次生成几条创意？", 1, 20, 5) # 默认5条，最高20条

if st.button(f"🔥 立即生成 {count} 条爆款组合", type="primary"):
    s, sty, p, v = load_words("subjects"), load_words("styles"), load_words("placements"), load_words("vibes")
    if s and sty and p and v:
        st.balloons()
        for i in range(count):
            res_s, res_sty, res_p, res_v = random.choice(s), random.choice(sty), random.choice(p), random.choice(v)
            with st.expander(f"查看第 {i+1} 条：{res_sty}风{res_s}"):
                st.write(f"**视觉逻辑：** 一个【{res_sty}】风格的【{res_s}】，适合贴在【{res_p}】，质感表现为【{res_v}】")
                st.code(f"Prompt: {res_s}, {res_sty} tattoo style, {res_v}, on {res_p}, white background, 8k resolution --v 6.0")
    else:
        st.warning("零件还不够，快去左边多录入点样板！")