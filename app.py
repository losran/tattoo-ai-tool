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
# --- 模块二：大爆炸预览区 ---
if st.session_state.pre_tags:
    st.write("---")
    st.subheader("💥 灵感大爆炸")
    st.caption("点击勾选你想要保存的关键词碎片：")
    
    # 建立一个容器，让标签排布更紧凑
    save_list = []
    
    # [1] 按照分类排放碎块
    for cat_name in ["主体", "风格", "部位", "氛围"]:
        # 过滤出属于当前分类的词
        cat_words = [t for t in st.session_state.pre_tags if t['cat'] == cat_name]
        
        if cat_words:
            st.markdown(f"**📍 {cat_name}**")
            # 创建多列，让词条像碎片一样横向炸开
            cols = st.columns(4) 
            for idx, tag in enumerate(cat_words):
                # 每一个词都是一个独立的 Checkbox
                with cols[idx % 4]:
                    if st.checkbox(tag['val'], value=True, key=f"boom_{cat_name}_{idx}"):
                        save_list.append(tag)
            st.write("") # 间距

    # [2] 操作按钮组
    st.write("")
    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button("🚀 将勾选碎片存入仓库", type="primary", use_container_width=True):
            if save_list:
                f_map = {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}
                for t in save_list:
                    if t['val'] not in st.session_state.db[t['cat']]:
                        st.session_state.db[t['cat']].append(t['val'])
                        sync_git(f_map[t['cat']], st.session_state.db[t['cat']])
                st.session_state.pre_tags = [] # 清空大爆炸现场
                st.success(f"成功录入 {len(save_list)} 个新素材！")
                time.sleep(1)
                st.rerun()
            else:
                st.warning("请至少勾选一个词条")
    with c2:
        if st.button("🧹 扫走碎片", use_container_width=True):
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

