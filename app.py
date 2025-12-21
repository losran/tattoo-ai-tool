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

# --- 2. 强化：云端文件强制写入 ---
def force_sync_github(category, word_list):
    # 精准映射文件名
    file_map = {"主体": "data/subjects.txt", "风格": "data/styles.txt", "部位": "data/placements.txt", "氛围": "data/vibes.txt"}
    path = file_map.get(category)
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # 获取 SHA，如果文件不存在则报错
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        sha = r.json()['sha']
        new_content = "\n".join(list(set(word_list))) # 自动去重
        payload = {
            "message": f"Sync {category}",
            "content": base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
            "sha": sha
        }
        requests.put(url, headers=headers, json=payload)
    else:
        st.error(f"GitHub 文件缺失: {path}，请确保 data 文件夹下有这个文件。")

# --- 3. 初始加载：启动即读取云端数据 ---
def load_all_data():
    db = {"主体": [], "风格": [], "部位": [], "氛围": []}
    files = {"主体": "data/subjects.txt", "风格": "data/styles.txt", "部位": "data/placements.txt", "氛围": "data/vibes.txt"}
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    for cat, path in files.items():
        url = f"https://api.github.com/repos/{REPO}/contents/{path}"
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            content = base64.b64decode(r.json()['content']).decode('utf-8')
            db[cat] = [line.strip() for line in content.splitlines() if line.strip()]
    return db

# 仅在会话开始时加载
if 'db' not in st.session_state:
    st.session_state.db = load_all_data()

# --- 4. 侧边栏：提取与强制分类 ---
with st.sidebar:
    st.header("📥 智能入库")
    input_box = st.text_area("粘贴样板描述", height=150, key="raw_input")
    
    if st.button("开始拆解并同步", type="primary", use_container_width=True):
        if input_box:
            with st.spinner('AI 正在处理并写入云端...'):
                # 向 DeepSeek 发出死命令：严禁废话
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": "分类仅限:主体,风格,部位,氛围。格式:分类:内容|分类:内容。不要括号，不要分组，直接给零件名称。"}]
                ).choices[0].message.content
                
                # 暴力解析：只要字符串包含关键字就归类
                parts = res.replace("\n", "").split("|")
                for p in parts:
                    if ":" in p:
                        k, v = p.split(":", 1)
                        val = v.strip()
                        target = None
                        if "主体" in k: target = "主体"
                        elif "风格" in k: target = "风格"
                        elif "部位" in k: target = "部位"
                        elif "氛围" in k: target = "氛围"
                        
                        if target and val not in st.session_state.db[target]:
                            st.session_state.db[target].append(val)
                            force_sync_github(target, st.session_state.db[target]) # 实时写盘
                
                st.success("入库成功！")
                st.rerun()

# --- 5. 主看板：极简胶囊布局 ---
st.title("🎨 纹身资产库看板")
cols = st.columns(4)
sections = ["主体", "风格", "部位", "氛围"]

for i, sec in enumerate(sections):
    with cols[i]:
        st.markdown(f"### {sec}")
        for word in st.session_state.db[sec]:
            # 采用你喜欢的蓝色胶囊 UI
            st.markdown(f"""
                <div style="display:inline-flex; align-items:center; background:rgba(0,113,227,0.1); 
                color:#0071e3; padding:2px 10px; border-radius:100px; margin:4px; font-size:13px; border:1px solid rgba(0,113,227,0.2);">
                    {word}
                </div>
            """, unsafe_allow_html=True)
            # 删除按钮紧随其后
            if st.button("×", key=f"del_{sec}_{word}_{random.random()}"):
                st.session_state.db[sec].remove(word)
                force_sync_github(sec, st.session_state.db[sec])
                st.rerun()

st.markdown("<br><hr>", unsafe_allow_html=True)
# (灵感生成部分代码保持不变...)
