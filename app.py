import streamlit as st
from openai import OpenAI
import random, requests, base64, time

# --- 1. 基础配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="纹身助手-稳固版", layout="centered")

# --- 2. 核心数据同步函数 ---
def sync_git(fn, data):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    hd = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(url, headers=hd).json()
        clean_data = [d.strip() for d in data if d and d.strip()]
        content = base64.b64encode("\n".join(list(set(clean_data))).encode()).decode()
        requests.put(url, headers=hd, json={"message": "sync", "content": content, "sha": r.get('sha')})
    except: pass

def get_git(fn):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if r.status_code == 200:
        return [l.strip() for l in base64.b64decode(r.json()['content']).decode('utf-8').splitlines() if l.strip()]
    return []

# 初始化状态
if 'db' not in st.session_state:
    st.session_state.db = {k: get_git(v) for k, v in {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}.items()}
if 'pre_tags' not in st.session_state: st.session_state.pre_tags = []
if 'input_id' not in st.session_state: st.session_state.input_id = 0

# --- 3. 界面逻辑 ---
st.title("🌀 纹身素材智能入库")

# 侧边栏只放数据统计，不放按钮
with st.sidebar:
    st.header("📊 资产统计")
    for k, v in st.session_state.db.items():
        st.metric(k, len(v))

# 模块一：智能拆分
st.subheader("第一步：样板拆解")
user_input = st.text_area("粘贴样板文案", height=150, placeholder="描述文本...", key=f"in_{st.session_state.input_id}")

if st.button("🔍 开始 AI 拆分", type="primary", use_container_width=True):
    if user_input:
        with st.spinner("AI 解析中..."):
            try:
                # 强化 Prompt 确保格式
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "你只输出标签。格式：分类:词|分类:词。分类限：主体、风格、部位、氛围。"},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.1
                ).choices[0].message.content
                
                # 容错解析
                parsed = []
                for p in res.replace("：", ":").replace("\n", "").split("|"):
                    if ":" in p:
                        k, v = p.split(":", 1)
                        if k.strip() in ["主体", "风格", "部位", "氛围"]:
                            parsed.append({"cat": k.strip(), "val": v.strip()})
                
                if parsed:
                    st.session_state.pre_tags = parsed
                    st.session_state.input_id += 1 # 清空输入框
                    st.rerun()
                else:
                    st.warning(f"解析失败。AI原文：{res}")
            except Exception as e:
                st.error(f"出错：{e}")

# 模块二：预览与入库
if st.session_state.pre_tags:
    st.write("---")
    st.subheader("第二步：确认入库")
    
    save_list = []
    for i, tag in enumerate(st.session_state.pre_tags):
        if st.checkbox(f"【{tag['cat']}】{tag['val']}", value=True, key=f"chk_{i}"):
            save_list.append(tag)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 一键入库", type="primary", use_container_width=True):
            f_map = {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}
            for t in save_list:
                if t['val'] not in st.session_state.db[t['cat']]:
                    st.session_state.db[t['cat']].append(t['val'])
                    sync_git(f_map[t['cat']], st.session_state.db[t['cat']])
            st.session_state.pre_tags = []
            st.success("已成功同步！")
            st.rerun()
    with col2:
        if st.button("🧹 放弃清空", use_container_width=True):
            st.session_state.pre_tags = []
            st.rerun()

# 模块三：简易仓库管理
st.write("---")
st.subheader("📚 仓库查看")
cat = st.selectbox("分类选择", ["主体", "风格", "部位", "氛围"])
items = st.session_state.db.get(cat, [])
if items:
    st.write("、".join(items)) # 用顿号隔开显示
else:
    st.caption("暂无数据")
