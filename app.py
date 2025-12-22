import streamlit as st
from openai import OpenAI
import random, requests, base64, time

# --- 1. 配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Pro Station", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 增强型 CSS (强制显示所有组件) ---
st.markdown("""
    <style>
    .main { background-color: #0d0d0d; }
    [data-testid="stColumn"]:nth-child(1) { position: fixed; left: 0; top: 0; bottom: 0; width: 120px !important; background: #161b22; z-index: 1001; padding: 40px 10px !important; border-right: 1px solid #333; }
    [data-testid="stColumn"]:nth-child(2) { margin-left: 140px !important; margin-right: 400px !important; width: auto !important; padding: 40px !important; }
    [data-testid="stColumn"]:nth-child(3) { position: fixed; right: 0; top: 0; bottom: 0; width: 380px !important; background: #0d1117; z-index: 1000; padding: 40px 20px !important; border-left: 1px solid #333; overflow-y: auto; }
    
    /* 确保 Checkbox 醒目可见 */
    .stCheckbox { background: #1f2428 !important; border: 1px solid #444 !important; padding: 10px !important; border-radius: 8px !important; margin-bottom: 5px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 稳健的数据同步 ---
def sync_git(fn, data):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    hd = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=hd).json()
    sha = r.get('sha')
    content = base64.b64encode("\n".join(list(set(data))).encode()).decode()
    requests.put(url, headers=hd, json={"message": "sync", "content": content, "sha": sha})

def get_git(fn):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    return base64.b64decode(r.json()['content']).decode('utf-8').splitlines() if r.status_code == 200 else []

# 状态初始化
if 'db' not in st.session_state:
    st.session_state.db = {k: get_git(v) for k, v in {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt","收藏":"favorites.txt"}.items()}
if 'is_split' not in st.session_state: st.session_state.is_split = False
if 'pre_tags' not in st.session_state: st.session_state.pre_tags = []

# --- 4. 三栏布局 ---
col_nav, col_mid, col_lib = st.columns([12, 53, 35])

with col_nav:
    st.markdown("### 🌀")
    for k in ["主体", "风格", "部位", "氛围"]:
        st.write(f"**{k}**")
        st.code(len(st.session_state.db.get(k, [])), language=None)

with col_mid:
    st.title("✨ 智能提取入库")
    raw = st.text_area("输入样板提示词", height=150, placeholder="粘贴文本后点击拆分...", key="main_input")
    
    if not st.session_state.is_split:
        if st.button("🔍 开始 AI 拆分", type="primary", use_container_width=True):
            if raw:
                with st.spinner("AI 正在解析..."):
                    try:
                        # 强制 AI 输出更规范的格式
                        res = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[
                                {"role": "system", "content": "你只输出标签，格式如下：分类:内容|分类:内容。分类必须从'主体,风格,部位,氛围'中选。"},
                                {"role": "user", "content": raw}
                            ],
                            temperature=0.1 # 降低随机性
                        ).choices[0].message.content
                        
                        # 诊断日志：如果出错，请把下面这行显示的文字截图给我
                        # st.write("AI原始返回:", res) 
                        
                        # 强力解析
                        temp_results = []
                        parts = res.replace("\n", "").split("|")
                        for p in parts:
                            if ":" in p:
                                k, v = p.split(":", 1)
                                cat = next((x for x in ["主体","风格","部位","氛围"] if x in k), None)
                                if cat:
                                    temp_results.append({"cat": cat, "val": v.strip(), "ok": True})
                        
                        if temp_results:
                            st.session_state.pre_tags = temp_results
                            st.session_state.is_split = True
                            st.rerun()
                        else:
                            st.error("AI未能识别出有效标签，请尝试换一段描述。")
                    except Exception as e:
                        st.error(f"API调用出错: {e}")

    else:
        st.markdown("### 📋 确认拆解结果")
        st.caption("勾选你想要保存的标签：")
        
        save_items = []
        # 强制遍历渲染
        for i, tag in enumerate(st.session_state.pre_tags):
            # 这里的 Key 必须唯一且持久
            is_checked = st.checkbox(f"【{tag['cat']}】 {tag['val']}", value=True, key=f"fixed_preview_{i}")
            if is_checked:
                save_items.append(tag)
        
        st.write("")
        c_save, c_reset = st.columns(2)
        with c_save:
            if st.button("🚀 一键入云库", type="primary", use_container_width=True):
                f_map = {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}
                for item in save_items:
                    if item['val'] not in st.session_state.db[item['cat']]:
                        st.session_state.db[item['cat']].append(item['val'])
                        sync_git(f_map[item['cat']], st.session_state.db[item['cat']])
                st.session_state.is_split = False
                st.session_state.pre_tags = []
                st.success("入库成功！")
                st.rerun()
        with c_reset:
            if st.button("🧹 撤销并清空", use_container_width=True):
                st.session_state.is_split = False
                st.session_state.pre_tags = []
                st.rerun()

with col_lib:
    st.subheader("📚 资产仓库")
    view_cat = st.selectbox("当前查看：", ["主体", "风格", "部位", "氛围"], label_visibility="collapsed")
    st.divider()
    items = st.session_state.db.get(view_cat, [])
    for word in items:
        r = st.columns([6, 1])
        r[0].write(f"`{word}`")
        if r[1].button("🗑️", key=f"del_{word}"):
            st.session_state.db[view_cat].remove(word)
            sync_git({"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}[view_cat], st.session_state.db[view_cat])
            st.rerun()
