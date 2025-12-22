import streamlit as st
from openai import OpenAI
import random, requests, base64, time

# --- 1. 配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Pro Station", layout="wide", initial_sidebar_state="collapsed")

# --- 2. CSS 布局 (左侧纯净，按钮归位) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .main { background-color: #0d0d0d; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    
    /* [1] 左侧固定导航 (只放 Logo 和 统计) */
    [data-testid="stColumn"]:nth-child(1) {
        position: fixed; left: 0; top: 0; bottom: 0;
        width: 120px !important;
        background: #161b22;
        border-right: 1px solid #333;
        z-index: 1001;
        padding-top: 30px !important;
        text-align: center;
    }

    /* 左下角统计 */
    .sticky-stats { position: fixed; left: 10px; bottom: 20px; width: 100px; z-index: 1002; }
    .nav-item { background: rgba(255,255,255,0.03); border:1px solid #333; border-radius:8px; margin-top:8px; padding:5px; }
    .nav-val { color: #58a6ff; font-weight:bold; font-size:16px; }
    .nav-lbl { color: #888; font-size:10px; }

    /* [2] 中间操作区 (输入框 + 结果) */
    [data-testid="stColumn"]:nth-child(2) {
        margin-left: 140px !important; margin-right: 380px !important;
        width: auto !important; padding: 40px !important;
    }

    /* [3] 右侧资产库 */
    [data-testid="stColumn"]:nth-child(3) {
        position: fixed; right: 0; top: 0; bottom: 0;
        width: 360px !important;
        background: #0d1117; border-left: 1px solid #333;
        padding: 30px 20px !important; z-index: 1000; overflow-y: auto;
    }

    /* 样式微调 */
    .stTextArea textarea { background-color: #161b22; color: #fff; border: 1px solid #333; }
    .preview-box { background: #1a1a1a; border: 1px solid #333; border-radius: 12px; padding: 20px; margin-top: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 数据逻辑 ---
def sync_git(fn, data):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    hd = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(url, headers=hd).json()
        sha = r.get('sha')
        content = base64.b64encode("\n".join(list(set(data))).encode()).decode()
        requests.put(url, headers=hd, json={"message": "sync", "content": content, "sha": sha})
    except: pass

def get_git(fn):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    return base64.b64decode(r.json()['content']).decode('utf-8').splitlines() if r.status_code == 200 else []

# 初始化
if 'db' not in st.session_state:
    st.session_state.db = {k: get_git(v) for k, v in {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt","收藏":"favorites.txt"}.items()}
if 'pre_tags' not in st.session_state: st.session_state.pre_tags = []
# 这里的 input_id 是清空输入框的关键
if 'input_id' not in st.session_state: st.session_state.input_id = 0

# --- 4. 布局 ---
col_nav, col_mid, col_lib = st.columns([12, 53, 35])

# 👉 左：只放 Logo 和 统计
with col_nav:
    st.markdown("### 🌀")
    stats_html = '<div class="sticky-stats">'
    for k in ["主体", "风格", "部位", "氛围"]:
        num = len(st.session_state.db.get(k, []))
        stats_html += f'<div class="nav-item"><div class="nav-lbl">{k}</div><div class="nav-val">{num}</div></div>'
    stats_html += '</div>'
    st.markdown(stats_html, unsafe_allow_html=True)

# 👉 中：输入 + 预览 + 入库
with col_mid:
    st.title("✨ 智能提取入库")
    
    # [1] 输入区域：使用动态 Key 实现清空
    # key=f"in_{st.session_state.input_id}" 每次 input_id +1，输入框就会重置
    raw_text = st.text_area("输入样板提示词", height=150, placeholder="在此粘贴文本，点击下方拆分...", key=f"in_{st.session_state.input_id}")
    
    # 拆分按钮紧跟输入框
    if st.button("🔍 开始 AI 拆分", type="primary"):
        if raw_text:
            with st.spinner("AI 解析中..."):
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": "格式:分类:词|分类:词。分类限:主体,风格,部位,氛围。"}, {"role": "user", "content": raw_text}]
                ).choices[0].message.content
                st.session_state.pre_tags = [{"cat": p.split(":")[0], "val": p.split(":")[1], "ok": True} for p in res.split("|") if ":" in p]
                
                # 关键：拆分成功后，让 ID + 1，下次刷新时输入框就空了
                st.session_state.input_id += 1 
                st.rerun()

    # [2] 结果预览区域 (如果有数据才显示)
    if st.session_state.pre_tags:
        st.markdown("<div class='preview-box'>", unsafe_allow_html=True)
        st.subheader("📋 确认拆解结果")
        st.caption("勾选要保存的标签：")
        
        save_list = []
        for i, tag in enumerate(st.session_state.pre_tags):
            if st.checkbox(f"【{tag['cat']}】{tag['val']}", value=True, key=f"t_{i}"):
                save_list.append(tag)
        
        st.write("---")
        
        # 底部按钮栏
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("🧹 放弃并清除结果", use_container_width=True):
                st.session_state.pre_tags = []
                st.rerun()
        with c2:
            # 这个按钮现在稳稳地在中间栏的右下侧
            if st.button("🚀 一键入云库", type="primary", use_container_width=True):
                f_map = {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}
                for t in save_list:
                    if t['val'] not in st.session_state.db[t['cat']]:
                        st.session_state.db[t['cat']].append(t['val'])
                        sync_git(f_map[t['cat']], st.session_state.db[t['cat']])
                st.session_state.pre_tags = [] # 入库后清除预览
                st.success(f"已成功存入 {len(save_list)} 个标签！")
                time.sleep(1)
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

# 👉 右：资产仓库
with col_lib:
    st.markdown("### 📚 资产仓库")
    view_cat = st.selectbox("当前查看分类：", ["主体", "风格", "部位", "氛围"], label_visibility="collapsed")
    st.divider()
    
    items = st.session_state.db.get(view_cat, [])
    if items:
        for word in items:
            c_tag, c_btn1, c_btn2 = st.columns([6, 1, 1])
            c_tag.markdown(f'<div style="background:#1f1f1f; padding:5px 10px; border-radius:6px; font-size:13px; border:1px solid #333;">{word}</div>', unsafe_allow_html=True)
            if c_btn1.button("⭐", key=f"fav_{word}"): pass
            if c_btn2.button("🗑️", key=f"del_{word}"):
                st.session_state.db[view_cat].remove(word)
                sync_git({"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}[view_cat], st.session_state.db[view_cat])
                st.rerun()
    else:
        st.caption("暂无内容")
