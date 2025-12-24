import streamlit as st
import random
import requests
import base64
from openai import OpenAI
from style_manager import apply_pro_style

# ================= 基础配置 =================
apply_pro_style()
st.set_page_config(layout="wide", page_title="Creative Engine")

client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

WAREHOUSE = {
    "Subject": "data/subjects.txt",
    "Action": "data/actions.txt",
    "Mood": "data/moods.txt",
    "Usage": "data/usage.txt",
    "StyleSystem": "data/styles_system.txt",
    "Technique": "data/styles_technique.txt",
    "Color": "data/styles_color.txt",
    "Texture": "data/styles_texture.txt",
    "Composition": "data/styles_composition.txt",
    "Accent": "data/styles_accent.txt"
}

GALLERY_FILE = "gallery/inspirations.txt"

# ================= 工具函数 =================
def get_github_data(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return [
                l.strip()
                for l in base64.b64decode(r.json()["content"]).decode().splitlines()
                if l.strip()
            ]
    except:
        pass
    return []

def chaos_pick(c, low, mid, high):
    if c < 30:
        return random.randint(*low)
    elif c < 70:
        return random.randint(*mid)
    else:
        return random.randint(*high)

def smart_sample(category, inventory, chaos):
    if not inventory:
        return []
    k = min(len(inventory), max(3, chaos // 20))
    return random.sample(inventory, k)

# ================= Session =================
for k in ["generated_cache", "selected_prompts", "polished_text"]:
    if k not in st.session_state:
        st.session_state[k] = []

# ================= UI =================
st.title("🎨 创意引擎")

chaos_level = st.slider("混乱度", 0, 100, 55)
num = st.number_input("生成数量", 1, 10, 6)
style_tone = st.selectbox("风格倾向", ["日式传统", "Old School", "New School", "极简"])
intent_input = st.text_area("意图输入", placeholder="比如：青蛙，日式 old school")

execute_button = st.button("🔥 激发创意组合", type="primary", use_container_width=True)

# ================= 执行生成 =================
if execute_button:
    db = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
    new_batch = []

    for _ in range(num):
        s = random.sample(db["Subject"], 1)
        a = random.sample(
            db["Action"],
            chaos_pick(chaos_level, (1, 1), (1, 2), (2, 3))
        )
        m = random.sample(
            db["Mood"],
            chaos_pick(chaos_level, (1, 2), (2, 3), (3, 4))
        )
        u = random.sample(db["Usage"], 1)

        ss = random.sample(db["StyleSystem"], 1)
        stl = random.sample(
            db["Technique"],
            chaos_pick(chaos_level, (1, 2), (2, 3), (3, 4))
        )
        sc = random.sample(db["Color"], 1)
        sx = random.sample(
            db["Texture"],
            chaos_pick(chaos_level, (0, 1), (1, 1), (1, 2))
        )
        sp = random.sample(db["Composition"], 1)

        sa = []
        if chaos_level > 60 and db["Accent"]:
            sa = random.sample(db["Accent"], 1)

        new_batch.append(
            f"{'，'.join(s)}，"
            f"{'，'.join(ss)}，{'，'.join(stl)}，{'，'.join(sc)}，"
            f"{'，'.join(sx)}，{'，'.join(sp)}，"
            f"{'，'.join(a)}，{'，'.join(m)}，"
            + (f"{'，'.join(sa)}，" if sa else "")
            + f"纹在{'，'.join(u)}"
        )

    st.session_state.generated_cache = new_batch
    st.rerun()

# ================= 展示 =================
if st.session_state.generated_cache:
    st.divider()
    st.subheader("🎲 生成结果")
    for i, p in enumerate(st.session_state.generated_cache):
        st.write(f"{i+1}. {p}")
