import streamlit as st
from openai import OpenAI
import random
import requests
import base64
import time

# --- 1. 配置与密钥 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo AI Workbench", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 深度定制 CSS (实现 SaaS 界面质感) ---
st.markdown("""
    <style>
    /* 全局背景深色 */
    .stApp { background-color: #0e1117; color: #fff; }
    
    /* 左侧操作区容器 */
    .workspace-container {
        background: #161b22;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #30363d;
        height: 85vh; /* 固定高度，模拟软件界面 */
        overflow-y: auto;
    }
    
    /* 右侧资产库容器 */
    .library-container {
        background: #0d1117;
        padding: 20px;
        border-radius: 12px;
        border-left: 1px solid #30363d;
        height: 85vh;
        overflow-y: auto;
    }
    
    /* 标题与LOGO */
    .app-logo { font-size: 24px; font-weight: 800; color: #4facfe; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
    
    /* 标签样式 (Chip) */
    .chip-item {
        display: inline-flex;
        align-items: center;
        background: #1f2428;
        border: 1px solid #30363d;
        color: #c9d1d9;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        margin: 4px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .chip-item:hover { border-color: #4facfe; color: #4facfe; }
    .chip-fav { border-color: #ffd700 !important; color: #ffd700 !important; }
    
    /* 选中态的标签 (用于入库确认) */
    .chip-selected { background: rgba(79, 172, 254, 0.2); border-color: #4facfe; color: white; }
    
    /* 统计数据 */
    .stat-row { display: flex; gap: 15px; margin-bottom: 20px; }
    .stat-card { background: #21262d; padding: 10px; border-radius: 8px; flex: 1; text-align: center; border: 1px solid #30363d; }
    .stat-num { font-size: 18px; font-weight: bold; color: #fff; }
    .stat-label { font-size: 11px; color: #8b949e; }
    
    /* 生成结果卡片 */
    .prompt-box { background: #000; padding: 15px; border-radius: 8px; border: 1px solid #333; margin-bottom: 10px; font-family: monospace; color: #0f0; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 云端同步核心 (含收藏) ---
def sync_file(filename, content_list):
    path = f"data/{filename}"
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(url, headers=headers)
        sha = r.json().get('sha')
        # 无论如何都转成字符串并去重
        clean_content = "\n".join(list(set([str(x).strip() for x in content_list if str(x).strip()])))
        payload = {
            "message": f"Update {filename}",
            "content": base64.b64encode(clean_content.encode('utf-8')).decode('utf-8')
        }
        if sha: payload['sha'] = sha
        requests.put(url, headers=headers, json=payload)
    except Exception as e:
        st.error(f"Sync Error: {e}")

# --- 4. 数据加载 ---
def load_db():
    files = {"主体": "subjects.txt", "风格": "styles.txt", "部位": "placements.txt", "氛围": "vibes.txt", "收藏": "favorites.txt"}
    db = {k: [] for k in files}
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    for cat, fname in files.items():
        try:
            url = f"https://api.github.com/repos/{REPO}/contents/data/{fname}"
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                content = base64.b64decode(r.json()['content']).decode('utf-8')
                db[cat] = [line.strip() for line in content.splitlines() if line.strip()]
        except: pass
    return db

if 'db' not in st.session_state:
    st.session_state.db = load_db()

# 状态管理：用于暂存 AI 拆解后但还没入库的词
if 'temp_tags' not in st.session_state:
    st.session_state.temp_tags = [] 

# --- 5. 界面布局 (左右 4:6 分栏) ---
col_left, col_right = st.columns([4, 6])

# ================================
# 👉 左侧：操作工作台 (Workspace)
# ================================
with col_left:
    st.markdown('<div class="workspace-container">', unsafe_allow_html=True)
    st.markdown('<div class="app-logo">🎨 Tattoo AI Pro</div>', unsafe_allow_html=True)
    
    # 顶部导航切换 (Segmented Control 风格)
    mode = st.radio("功能选择", ["智能入库", "生成提示词"], horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    # --- 场景 A: 智能入库 ---
    if mode == "智能入库":
        st.subheader("📥 样板拆解")
        raw_text = st.text_area("粘贴描述文本", height=100, placeholder="例如：Old School风格的老虎，满背，霸气...")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⚡ 开始拆解", type="primary", use_container_width=True):
                if raw_text:
                    with st.spinner("AI 正在分析..."):
                        # 调用 AI
                        res = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "system", "content": "提取纹身词。格式:分类:内容。分类限:主体,风格,部位,氛围。"}, 
                                      {"role": "user", "content": raw_text}]
                        ).choices[0].message.content
                        
                        # 解析并存入临时区 (temp_tags)，此时不入库！
                        st.session_state.temp_tags = []
                        for p in res.replace("\n","|").split("|"):
                            if ":" in p:
                                k, v = p.split(":", 1)
                                cat = next((x for x in ["主体","风格","部位","氛围"] if x in k), None)
                                if cat:
                                    # 默认全选 (checked=True)
                                    st.session_state.temp_tags.append({"cat": cat, "val": v.strip(), "checked": True})
        with c2:
            if st.button("🗑️ 清空输入", use_container_width=True):
                st.session_state.temp_tags = []
                st.rerun()

        # --- 确认入库区 (这是你最想要的功能) ---
        if st.session_state.temp_tags:
            st.divider()
            st.caption(f"识别到 {len(st.session_state.temp_tags)} 个标签，请勾选确认：")
            
            # 使用 checkbox 列表让用户选择
            updated_tags = []
            for i, tag in enumerate(st.session_state.temp_tags):
                # 渲染复选框
                is_checked = st.checkbox(f"【{tag['cat']}】{tag['val']}", value=tag['checked'], key=f"check_{i}")
                tag['checked'] = is_checked
                updated_tags.append(tag)
            
            # 更新状态
            st.session_state.temp_tags = updated_tags
            
            st.write("")
            if st.button("💾 确认入库 (仅选中项)", type="primary", use_container_width=True):
                count = 0
                file_map = {"主体": "subjects.txt", "风格": "styles.txt", "部位": "placements.txt", "氛围": "vibes.txt"}
                
                for tag in st.session_state.temp_tags:
                    if tag['checked']: # 只有勾选的才存
                        cat = tag['cat']
                        val = tag['val']
                        if val not in st.session_state.db[cat]:
                            st.session_state.db[cat].append(val)
                            sync_file(file_map[cat], st.session_state.db[cat])
                            count += 1
                
                st.success(f"成功存入 {count} 个新词！")
                st.session_state.temp_tags = [] # 清空待选区
                time.sleep(1)
                st.rerun()

    # --- 场景 B: 生成提示词 ---
    elif mode == "生成提示词":
        st.subheader("🎨 灵感生成")
        
        # 参考图上传 (视觉占位)
        st.file_uploader("参考图 (可选)", type=["jpg", "png"], help="AI将参考图片构图(开发中)")
        
        # 数量选择
        gen_count = st.select_slider("生成数量", options=[1, 3, 5, 10], value=3)
        
        if st.button("🚀 立即生成", type="primary", use_container_width=True):
            st.divider()
            for i in range(gen_count):
                # 随机抽取
                s = random.choice(st.session_state.db["主体"]) if st.session_state.db["主体"] else "Tattoo"
                sty = random.choice(st.session_state.db["风格"]) if st.session_state.db["风格"] else "Artistic"
                p = random.choice(st.session_state.db["部位"]) if st.session_state.db["部位"] else "Body"
                v = random.choice(st.session_state.db["氛围"]) if st.session_state.db["氛围"] else "Cool"
                
                prompt = f"/imagine prompt: {s}, {sty} style, {v} vibe, on {p} --v 6.0"
                
                st.markdown(f"""
                <div class="prompt-box">
                    <div style="color:#888; font-size:12px; margin-bottom:5px;">方案 #{i+1} ({sty} · {s})</div>
                    {prompt}
                </div>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # End Workspace

# ================================
# 👉 右侧：资产库存 (Library)
# ================================
with col_right:
    st.markdown('<div class="library-container">', unsafe_allow_html=True)
    
    # 顶部统计栏
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card"><div class="stat-num">{len(st.session_state.db['主体'])}</div><div class="stat-label">主体</div></div>
        <div class="stat-card"><div class="stat-num">{len(st.session_state.db['风格'])}</div><div class="stat-label">风格</div></div>
        <div class="stat-card"><div class="stat-num">{len(st.session_state.db['部位'])}</div><div class="stat-label">部位</div></div>
        <div class="stat-card"><div class="stat-num">{len(st.session_state.db['氛围'])}</div><div class="stat-label">氛围</div></div>
    </div>
    """, unsafe_allow_html=True)
    
    # 筛选与工具栏
    c_filter, c_fav = st.columns([3, 1])
    with c_filter:
        view_cat = st.selectbox("查看分类", ["主体", "风格", "部位", "氛围"], label_visibility="collapsed")
    with c_fav:
        only_fav = st.checkbox("❤️ 仅收藏")
    
    st.divider()
    
    # 列表展示逻辑
    items_to_show = st.session_state.db[view_cat]
    if only_fav:
        items_to_show = [i for i in items_to_show if i in st.session_state.db["收藏"]]
    
    if not items_to_show:
        st.info("这里还是空的，快去左边进货吧！")
    
    # 渲染标签列表 (每一行一个标签+操作按钮)
    for item in items_to_show:
        is_fav = item in st.session_state.db["收藏"]
        
        # 布局：列1(标签) | 列2(收藏) | 列3(删除)
        c1, c2, c3 = st.columns([6, 1, 1])
        
        with c1:
            # 标签视觉：如果是收藏的，边框变金黄色
            fav_class = "chip-fav" if is_fav else ""
            st.markdown(f'<div class="chip-item {fav_class}">{item}</div>', unsafe_allow_html=True)
            
        with c2:
            # 收藏按钮
            btn_label = "❤️" if is_fav else "🤍"
            if st.button(btn_label, key=f"fav_{view_cat}_{item}"):
                if is_fav: st.session_state.db["收藏"].remove(item)
                else: st.session_state.db["收藏"].append(item)
                sync_file("favorites.txt", st.session_state.db["收藏"])
                st.rerun()
                
        with c3:
            # 删除按钮
            if st.button("🗑️", key=f"del_{view_cat}_{item}"):
                st.session_state.db[view_cat].remove(item)
                # 还要把对应的文件同步更新
                map_name = {"主体": "subjects.txt", "风格": "styles.txt", "部位": "placements.txt", "氛围": "vibes.txt"}
                sync_file(map_name[view_cat], st.session_state.db[view_cat])
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True) # End Library
