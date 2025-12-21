import streamlit as st
from openai import OpenAI
import random
import requests
import base64

# --- 1. 配置与安全读取 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Studio Pro", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 核心：云端强制写入 ---
def sync_github(category, word_list):
    # 建立中文到文件名的绝对映射
    file_map = {
        "主体": "data/subjects.txt", 
        "风格": "data/styles.txt", 
        "部位": "data/placements.txt", 
        "氛围": "data/vibes.txt"
    }
    path = file_map.get(category)
    if not path: return

    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # 1. 获取当前文件信息（SHA）
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        file_data = r.json()
        sha = file_data['sha']
        # 2. 准备新内容（去重）
        new_content = "\n".join(list(set(word_list)))
        payload = {
            "message": f"Update {category}",
            "content": base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
            "sha": sha
        }
        # 3. 推送更新
        requests.put(url, headers=headers, json=payload)

# --- 3. 初始加载：启动即读取云端数据 ---
def load_data():
    db = {"主体": [], "风格": [], "部位": [], "氛围": []}
    file_map = {"主体": "data/subjects.txt", "风格": "data/styles.txt", "部位": "data/placements.txt", "氛围": "data/vibes.txt"}
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    for cat, path in file_map.items():
        url = f"https://api.github.com/repos/{REPO}/contents/{path}"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content = base64.b64decode(r.json()['content']).decode('utf-8')
            db[cat] = [line.strip() for line in content.splitlines() if line.strip()]
    return db

# 仅在第一次打开时加载
if 'db' not in st.session_state:
    st.session_state.db = load_data()

# --- 4. 视觉样式 (修复对齐问题) ---
st.markdown("""
    <style>
    .chip {
        display: inline-flex;
        align-items: center;
        background: rgba(0, 113, 227, 0.08);
        color: #0071e3 !important;
        padding: 4px 12px;
        border-radius: 100px;
        font-size: 13px;
        margin: 4px;
        border: 1px solid rgba(0, 113, 227, 0.1);
        font-weight: 500;
    }
    .res-card {
        background: rgba(128, 128, 128, 0.05);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.1);
        margin-bottom: 15px;
    }
    /* 删除按钮样式 */
    .stButton > button {
        border: none !important;
        background: transparent !important;
        color: #ff3b30 !important;
        padding: 0 !important;
        margin-left: -5px !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 5. 侧边栏：提取逻辑 (修复AI认知) ---
with st.sidebar:
    st.header("📥 智能入库")
    input_text = st.text_area("粘贴样板描述", height=150, key="raw_input")
    
    if st.button("开始拆解并同步", type="primary", use_container_width=True):
        if input_text:
            with st.spinner('AI 正在分析纹身元素...'):
                # 关键修改：强设定 Prompt，防止出现连衣裙
                system_prompt = """
                你是一个专业纹身设计师。请从描述中提取关键视觉元素。
                必须严格按此格式输出：主体:X|风格:X|部位:X|氛围:X
                示例：主体:龙|风格:日式传统|部位:满背|氛围:霸气
                严禁输出任何与纹身无关的内容（如衣服、家居等）。
                """
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": input_text}
                    ]
                ).choices[0].message.content
                
                # 解析逻辑
                parts = res.replace("\n", "").split("|")
                for p in parts:
                    if ":" in p:
                        k, v = p.split(":", 1)
                        clean_v = v.strip()
                        # 映射到四大类
                        target = None
                        if "主体" in k: target = "主体"
                        elif "风格" in k: target = "风格"
                        elif "部位" in k: target = "部位"
                        elif "氛围" in k: target = "氛围"
                        
                        # 存入并同步
                        if target and clean_v and clean_v not in st.session_state.db[target]:
                            st.session_state.db[target].append(clean_v)
                            sync_github(target, st.session_state.db[target])
                
                st.success("入库成功！")
                st.rerun()

# --- 6. 主看板显示 ---
st.title("🎨 纹身设计资产看板")

cols = st.columns(4)
sections = ["主体", "风格", "部位", "氛围"]

for i, sec in enumerate(sections):
    with cols[i]:
        st.markdown(f"### {sec}")
        for word in st.session_state.db[sec]:
            # 使用列布局来放置标签和删除按钮
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"<div class='chip'>{word}</div>", unsafe_allow_html=True)
            with c2:
                # 唯一的 Key 防止冲突
                if st.button("×", key=f"del_{sec}_{word}_{random.random()}"):
                    st.session_state.db[sec].remove(word)
                    sync_github(sec, st.session_state.db[sec])
                    st.rerun()

st.markdown("---")

# --- 7. 灵感批量生成 (这次绝对没丢！) ---
st.header("🎲 灵感批量生成")
count = st.select_slider("选择生成数量", options=[1, 3, 5, 8], value=3)

if st.button("✨ 立即生成创意组合", use_container_width=True):
    # 检查库存是否充足
    if all(len(v) > 0 for v in st.session_state.db.values()):
        st.balloons()
        res_cols = st.columns(2)
        for i in range(count):
            # 随机抽取
            s = random.choice(st.session_state.db["主体"])
            sty = random.choice(st.session_state.db["风格"])
            p = random.choice(st.session_state.db["部位"])
            v = random.choice(st.session_state.db["氛围"])
            
            with res_cols[i % 2]:
                st.markdown(f"""
                <div class="res-card">
                    <div style="color:#0071e3; font-size:12px; font-weight:700; margin-bottom:8px;">DESIGN CASE {i+1}</div>
                    <div style="font-size:18px; font-weight:600; margin-bottom:4px;">{sty}风格 - {s}</div>
                    <div style="font-size:14px; opacity:0.7; margin-bottom:12px;">建议部位：{p} | 氛围：{v}</div>
                    <div style="background:rgba(0,113,227,0.05); padding:10px; border-radius:6px; font-size:12px; font-family:monospace; color:#333;">
                        Prompt: {s}, {sty} tattoo style, {v} atmosphere, placed on {p}, white background, high detail --v 6.0
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ 零件库缺货！请先在左侧录入更多素材（至少每个分类有一个词）。")
