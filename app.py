import streamlit as st
from openai import OpenAI
import random, requests, base64, time

# --- 1. 配置与初始化 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Workbench", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 深度 UI 建模 (模拟你设计的黑色专业界面) ---
st.markdown("""
    <style>
    /* 核心背景与字体 */
    .stApp { background-color: #0e1117; color: #e6edf3; }
    
    /* 左侧 Logo 区域 */
    .logo-area { padding: 10px 0 30px 0; display: flex; align-items: center; gap: 10px; font-size: 22px; font-weight: 800; color: #4facfe; }
    
    /* 计数器小字 */
    .stat-text { font-size: 13px; color: #8b949e; margin-bottom: 5px; }
    
    /* 操作区卡片 */
    .op-card { background: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 12px; height: 85vh; }
    
    /* 右侧仓库样式 */
    .lib-container { background: #0d1117; border-left: 1px solid #30363d; padding: 20px; height: 85vh; overflow-y: auto; }
    
    /* 胶囊标签 (蓝色边框版) */
    .tag-chip {
        display: inline-flex; align-items: center; justify-content: space-between;
        background: rgba(0, 113, 227, 0.05); border: 1px solid rgba(0, 113, 227, 0.3);
        color: #58a6ff; padding: 4px 12px; border-radius: 6px; font-size: 13px; margin: 4px;
    }
    
    /* 提示词生成结果瀑布流 */
    .prompt-result { background: #000; border: 1px solid #333; padding: 15px; border-radius: 8px; margin-bottom: 15px; font-family: 'Courier New', monospace; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 数据读写补丁 ---
def io_git(fn, data=None, mode="r"):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    hd = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    if mode == "r":
        res = requests.get(url, headers=hd)
        return base64.b64decode(res.json()['content']).decode('utf-8').splitlines() if res.status_code==200 else []
    else:
        curr = requests.get(url, headers=hd).json()
        payload = {"message":"update","content":base64.b64encode("\n".join(list(set(data))).encode()).decode(),"sha":curr.get('sha')}
        requests.put(url, headers=hd, json=payload)

# 自动刷新数据库
if 'db' not in st.session_state:
    st.session_state.db = {k: io_git(v) for k, v in {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt","收藏":"favorites.txt"}.items()}
if 'temp_tags' not in st.session_state: st.session_state.temp_tags = []

# --- 4. 整体界面架构 (左右分栏 1:1) ---
main_left, main_right = st.columns([1, 1])

# ==========================================
# 👉 左侧：功能操作区 (智能入库 / 生成提示词)
# ==========================================
with main_left:
    st.markdown('<div class="logo-area">🌀 Tattoo AI Pro</div>', unsafe_allow_html=True)
    
    # 模仿你设计稿的左边侧栏计数 (放在功能按钮下方)
    c_sub, c_sty = len(st.session_state.db["主体"]), len(st.session_state.db["风格"])
    
    # 功能大切换按钮
    tab_in, tab_gen = st.tabs(["📥 智能提取入库", "🎲 生成提示词"])
    
    with tab_in:
        raw_text = st.text_area("粘贴样板描述", height=200, placeholder="描述文本...", key="in_box")
        
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("🔍 开始拆解", type="primary", use_container_width=True):
            if raw_text:
                with st.spinner("AI 正在解析标签..."):
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": "格式:分类:词|分类:词。分类限:主体,风格,部位,氛围。"}, {"role": "user", "content": raw_text}]
                    ).choices[0].message.content
                    st.session_state.temp_tags = []
                    for p in res.split("|"):
                        if ":" in p:
                            k, v = p.split(":", 1)
                            st.session_state.temp_tags.append({"cat": k.strip(), "val": v.strip(), "sel": True})
        
        if col_btn2.button("🧹 清空输入", use_container_width=True):
            st.session_state.temp_tags = []
            st.rerun()

        # --- 核心：你要求的“选择性入库”界面 ---
        if st.session_state.temp_tags:
            st.markdown("---")
            st.subheader("确认入库项")
            final_save_list = []
            for i, tag in enumerate(st.session_state.temp_tags):
                # 每一行显示分类和词，带复选框
                if st.checkbox(f"【{tag['cat']}】{tag['val']}", value=tag['sel'], key=f"check_{i}"):
                    final_save_list.append(tag)
            
            if st.button("✅ 确认入库选中标签", type="primary", use_container_width=True):
                f_map = {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}
                for item in final_save_list:
                    if item['val'] not in st.session_state.db[item['cat']]:
                        st.session_state.db[item['cat']].append(item['val'])
                        io_git(f_map[item['cat']], st.session_state.db[item['cat']], "w")
                st.session_state.temp_tags = []
                st.success("入库成功，已同步云端！")
                st.rerun()

    with tab_gen:
        st.subheader("创意生成")
        st.file_uploader("参考图 (可选)", type=["jpg", "png"])
        st.markdown("---")
        gen_num = st.select_slider("生成数量", options=[1, 3, 5, 8], value=1)
        
        if st.button("🚀 开始随机跑组合", type="primary", use_container_width=True):
            for i in range(gen_num):
                # 随机抽取
                s = random.choice(st.session_state.db["主体"]) if st.session_state.db["主体"] else "Subject"
                sty = random.choice(st.session_state.db["风格"]) if st.session_state.db["风格"] else "Style"
                p = random.choice(st.session_state.db["部位"]) if st.session_state.db["部位"] else "Body"
                v = random.choice(st.session_state.db["氛围"]) if st.session_state.db["氛围"] else "Vibe"
                
                st.markdown(f"""
                <div class="prompt-result">
                    <div style="color:#8b949e; font-size:11px;">#方案 {i+1}</div>
                    <b>{sty} · {s}</b><br>
                    <small>Prompt: {s}, {sty} tattoo, on {p}, {v} atmosphere --v 6.0</small>
                </div>
                """, unsafe_allow_html=True)

    # 左下角计数器
    st.sidebar.markdown(f"**主体统计:** {c_sub}")
    st.sidebar.markdown(f"**风格统计:** {c_sty}")

# ==========================================
# 👉 右侧：固定库存展示区 (Library)
# ==========================================
with main_right:
    st.markdown("### 📚 资产仓库")
    
    # 顶部工具栏
    tool_c1, tool_c2 = st.columns([2, 1])
    with tool_c1:
        view_cat = st.selectbox("分类", ["主体", "风格", "部位", "氛围"], label_visibility="collapsed")
    with tool_c2:
        only_fav = st.checkbox("仅收藏 ⭐")
    
    st.divider()
    
    # 渲染标签
    display_items = st.session_state.db[view_cat]
    if only_fav:
        display_items = [i for i in display_items if i in st.session_state.db["收藏"]]
    
    # 每行两个标签排版
    for i in range(0, len(display_items), 2):
        row_items = display_items[i : i+2]
        row_cols = st.columns(2)
        for idx, item in enumerate(row_items):
            is_fav = item in st.session_state.db["收藏"]
            with row_cols[idx]:
                # 胶囊 UI
                st.markdown(f'<div class="tag-chip"><span>{item}</span></div>', unsafe_allow_html=True)
                # 操作按钮
                b_c1, b_c2 = st.columns(2)
                if b_c1.button("⭐" if is_fav else "🤍", key=f"f_{item}"):
                    if is_fav: st.session_state.db["收藏"].remove(item)
                    else: st.session_state.db["收藏"].append(item)
                    io_git("favorites.txt", st.session_state.db["收藏"], "w")
                    st.rerun()
                if b_c2.button("🗑️", key=f"d_{item}"):
                    st.session_state.db[view_cat].remove(item)
                    f_name = {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}[view_cat]
                    io_git(f_name, st.session_state.db[view_cat], "w")
                    st.rerun()
