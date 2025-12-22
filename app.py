import streamlit as st
from openai import OpenAI
import random, requests, base64, time

# --- 1. 基础配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Pro Station", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 核心 CSS (强制三栏布局 + 碎片卡片化) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .main { background-color: #0d0d0d; color: #fff; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    /* 左侧：固定看板 */
    [data-testid="stColumn"]:nth-child(1) {
        position: fixed; left: 0; top: 0; bottom: 0; width: 120px !important;
        background: #161b22; border-right: 1px solid #333; z-index: 1001; padding-top: 20px !important;
    }
    .sticky-stats { position: fixed; left: 10px; bottom: 20px; width: 100px; z-index: 1002; }
    .nav-item { background: rgba(255,255,255,0.05); border: 1px solid #333; border-radius: 8px; padding: 8px; margin-top: 8px; text-align: center; }
    .nav-val { color: #58a6ff; font-weight: bold; font-size: 16px; }

    /* 中间：生产区 */
    [data-testid="stColumn"]:nth-child(2) {
        margin-left: 140px !important; margin-right: 380px !important;
        width: auto !important; padding: 40px !important;
    }

    /* 右侧：仓库区 (强制显示) */
    [data-testid="stColumn"]:nth-child(3) {
        position: fixed; right: 0; top: 0; bottom: 0; width: 360px !important;
        background: #0d1117; border-left: 1px solid #333; padding: 30px 20px !important;
        z-index: 1000; overflow-y: auto !important;
    }

    /* 碎片卡片样式 (大爆炸效果) */
    [data-testid="stCheckbox"] {
        background: #1f2428 !important; border: 1px solid #333 !important;
        padding: 5px 10px !important; border-radius: 6px !important; margin-bottom: 5px !important;
    }
    [data-testid="stCheckbox"]:has(input:checked) {
        border-color: #ff4b4b !important; background: #2d1b1b !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 数据同步 ---
def sync_git(fn, data):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    hd = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(url, headers=hd).json()
        content = base64.b64encode("\n".join(list(set(data))).encode()).decode()
        requests.put(url, headers=hd, json={"message": "sync", "content": content, "sha": r.get('sha')})
    except: pass

def get_git(fn):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    return base64.b64decode(r.json()['content']).decode('utf-8').splitlines() if r.status_code == 200 else []

if 'db' not in st.session_state:
    st.session_state.db = {k: get_git(v) for k, v in {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}.items()}
if 'pre_tags' not in st.session_state: st.session_state.pre_tags = []
if 'input_id' not in st.session_state: st.session_state.input_id = 0

# --- 4. 物理三栏渲染 ---
col_nav, col_mid, col_lib = st.columns([12, 53, 35])

# 👉 左：看板
with col_nav:
    st.markdown("### 🌀")
    html = '<div class="sticky-stats">'
    for k in ["主体", "风格", "部位", "氛围"]:
        html += f'<div class="nav-item"><div style="font-size:10px;color:#888">{k}</div><div class="nav-val">{len(st.session_state.db.get(k, []))}</div></div>'
    st.markdown(html + '</div>', unsafe_allow_html=True)

# 👉 中：生产大爆炸
# 👉 中：生产大爆炸 (整段替换)
with col_mid:
    st.title("✨ 灵感大爆炸拆解")
    
    # 1. 输入框
    raw = st.text_area("粘贴样板描述", height=150, key=f"in_{st.session_state.input_id}")
    
    # 2. 拆解按钮逻辑 (先执行逻辑，存入状态)
    if st.button("🔍 立即拆解", type="primary", use_container_width=True):
        if raw:
            with st.spinner("碎裂中..."):
                # --- [TEST: API 请求] ---
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "要求：Subject:词|Action:词|Style:词|Mood:词|Usage:词。词要拆得极细，禁止废话。"},
                        {"role": "user", "content": raw}
                    ],
                    temperature=0.1
                ).choices[0].message.content
                
                # --- [TEST: 解析清洗] ---
                parsed = []
                clean_res = res.replace("**", "").replace("：", ":").replace("\n", "|")
                for p in clean_res.split("|"):
                    if ":" in p:
                        k, v = p.split(":", 1)
                        # 兼容你指定的五维分类
                        found_cat = None
                        for target in ["Subject", "Action", "Style", "Mood", "Usage"]:
                            if target.lower() in k.lower(): found_cat = target; break
                        
                        if found_cat:
                            # 强力炸开碎片
                            bits = v.replace("、", "/").replace(",", "/").replace(" ", "/").split("/")
                            for b in bits:
                                if b.strip(): parsed.append({"cat": found_cat, "val": b.strip()})
                
                if parsed:
                    st.session_state.pre_tags = parsed
                    # 只有拆成功了才清空输入框
                    st.session_state.input_id += 1 
                    st.rerun() 
                else:
                    st.error(f"❌ 解析失败。AI原文：{res}")

    # 3. 🏁 碎片预览区 (必须在按钮外面，这样刷新后才能看见)
    if st.session_state.pre_tags:
        st.write("---")
        st.subheader("📋 碎片预览 (勾选想要入库的)")
        
        save_list = []
        # 按指定五维顺序展示
        order = ["Subject", "Action", "Style", "Mood", "Usage"]
        
        for display_cat in order:
            words = [t for t in st.session_state.pre_tags if t['cat'] == display_cat]
            if words:
                st.markdown(f"**📍 {display_cat}**")
                cols = st.columns(3)
                for i, w in enumerate(words):
                    with cols[i % 3]:
                        # 加上 input_id 确保 key 永远唯一，防止状态卡死
                        k = f"pre_{display_cat}_{i}_{st.session_state.input_id}"
                        if st.checkbox(w['val'], value=True, key=k):
                            save_list.append(w)
        
        # 4. 入库与清空操作
        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 一键入云库", type="primary", use_container_width=True):
                # 这里对接你的 sync_git 逻辑
                f_map = {"Subject":"subjects.txt","Action":"actions.txt","Style":"styles.txt","Mood":"moods.txt","Usage":"usage.txt"}
                for t in save_list:
                    if t['val'] not in st.session_state.db.get(t['cat'], []):
                        st.session_state.db.setdefault(t['cat'], []).append(t['val'])
                        sync_git(f_map.get(t['cat'], "misc.txt"), st.session_state.db[t['cat']])
                st.session_state.pre_tags = []
                st.success("同步成功")
                time.sleep(1); st.rerun()
        with c2:
            if st.button("🧹 扫走碎片", use_container_width=True):
                st.session_state.pre_tags = []
                st.rerun()

# 2. 立即拆解按钮 (五维大爆炸版)
    if st.button("🔍 立即炸开碎片", type="primary", use_container_width=True):
        if raw:
            with st.spinner("💥 正在执行五维深度拆解..."):
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": """你是一个专业的纹身提示词拆解专家。
                        请将文案打碎并归类到以下五个维度：
                        1. Subject (核心主体/名词)
                        2. Action (动作/姿态/具体状态)
                        3. Style (视觉风格/技法)
                        4. Mood (情绪/氛围感)
                        5. Usage (使用场景/部位建议)
                        输出格式：类别:词|类别:词。禁止废话，禁止星号。词要拆得极细。"""},
                        {"role": "user", "content": raw}
                    ],
                    temperature=0.1
                ).choices[0].message.content
                
                parsed = []
                # --- [TEST: 五维解析清洗] ---
                clean_text = res.replace("**", "").replace("：", ":").replace("\n", "|")
                parts = [p for p in clean_text.split("|") if ":" in p]
                
                # 定义标准分类映射
                cat_map = {
                    "Subject": "🦴 Subject",
                    "Action": "⚡ Action",
                    "Style": "🎨 Style",
                    "Mood": "🔮 Mood",
                    "Usage": "📌 Usage"
                }

                for p in parts:
                    k, v = p.split(":", 1)
                    # 匹配分类（支持中英文匹配）
                    found_cat = None
                    for eng, show in cat_map.items():
                        if eng.lower() in k.lower() or show in k:
                            found_cat = show
                            break
                    
                    if found_cat:
                        # 强力打碎：处理括号、顿号、逗号
                        sub_content = v.replace("（", "/").replace("）", "/").replace("、", "/").replace(",", "/").replace(" ", "/")
                        sub_words = [sw.strip() for sw in sub_content.split("/") if sw.strip()]
                        for sw in sub_words:
                            parsed.append({"cat": found_cat, "val": sw})
                
                if parsed:
                    st.session_state.pre_tags = parsed
                    st.session_state.input_id += 1
                    st.rerun()
                else:
                    st.error("❌ 诊断：五维解析未命中")
                    with st.expander("🛠️ Debug Test"):
                        st.write("AI原始回复：", res)
# 👉 右：仓库管理
with col_lib:
    st.subheader("📚 仓库整理")
    cat = st.selectbox("分类", ["主体", "风格", "部位", "氛围"], key="lib_cat", label_visibility="collapsed")
    st.divider()
    items = st.session_state.db.get(cat, [])
    del_list = []
    if items:
        lib_cols = st.columns(2)
        for i, item in enumerate(items):
            with lib_cols[i % 2]:
                if st.checkbox(item, value=False, key=f"lib_{cat}_{i}"):
                    del_list.append(item)
        if del_list:
            if st.button(f"🗑️ 批量删除 {len(del_list)} 项", type="secondary", use_container_width=True):
                st.session_state.db[cat] = [x for x in items if x not in del_list]
                sync_git({"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}[cat], st.session_state.db[cat])
                st.rerun()
    else: st.caption("空空如也")







