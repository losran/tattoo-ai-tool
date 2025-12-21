import streamlit as st
from openai import OpenAI
import random
import requests
import base64

# --- 1. 基础配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Studio Pro", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS 样式 (UI 核心：仿 App 质感) ---
st.markdown("""
    <style>
    /* 全局字体与背景优化 */
    .stApp { background-color: #0e1117; }
    
    /* 侧边栏计数器 */
    .counter-box {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        margin-bottom: 10px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .counter-num { font-size: 24px; font-weight: bold; color: #4facfe; }
    .counter-label { font-size: 12px; color: #aaa; }

    /* 标签 Chips */
    .chip-container { display: flex; flex-wrap: wrap; gap: 6px; }
    .chip {
        background: #1e2329;
        color: #e6e6e6;
        padding: 4px 12px;
        border-radius: 100px;
        font-size: 12px;
        border: 1px solid #30363d;
        display: inline-flex;
        align-items: center;
        margin-bottom: 4px;
    }
    .chip-fav { border-color: #ffd700; color: #ffd700; }
    
    /* 操作按钮微调 */
    .small-btn { font-size: 10px; margin-left: 5px; cursor: pointer; color: #666; }
    .small-btn:hover { color: #ff4b4b; }

    /* 生成结果卡片 */
    .prompt-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 云端同步逻辑 (含收藏功能) ---
def sync_github(filename, content_list):
    path = f"data/{filename}"
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    try:
        r = requests.get(url, headers=headers)
        sha = r.json().get('sha')
        # 清洗并去重
        clean_content = "\n".join(list(set([str(x).strip() for x in content_list if str(x).strip()])))
        
        payload = {
            "message": f"Update {filename}",
            "content": base64.b64encode(clean_content.encode('utf-8')).decode('utf-8')
        }
        if sha: payload['sha'] = sha
        requests.put(url, headers=headers, json=payload)
    except Exception as e:
        print(f"Sync Error: {e}")

# --- 4. 数据加载 ---
def load_data():
    files = {
        "主体": "subjects.txt", "风格": "styles.txt", 
        "部位": "placements.txt", "氛围": "vibes.txt",
        "收藏": "favorites.txt"
    }
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

# 初始化 Session
if 'db' not in st.session_state:
    st.session_state.db = load_data()
if 'preview_tags' not in st.session_state:
    st.session_state.preview_tags = [] # 用于暂存AI拆解结果

# --- 5. 侧边栏：导航与统计 ---
with st.sidebar:
    st.header("🌀 Tattoo AI Pro")
    
    # 模式切换
    mode = st.radio("工作模式", ["✨ 智能入库", "🎲 生成提示词"], label_visibility="collapsed")
    
    st.markdown("---")
    st.caption("📦 库存概览")
    
    # 实时计数器
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="counter-box"><div class="counter-num">{len(st.session_state.db["主体"])}</div><div class="counter-label">主体</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="counter-box"><div class="counter-num">{len(st.session_state.db["风格"])}</div><div class="counter-label">风格</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="counter-box"><div class="counter-num">{len(st.session_state.db["部位"])}</div><div class="counter-label">部位</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="counter-box"><div class="counter-num">{len(st.session_state.db["氛围"])}</div><div class="counter-label">氛围</div></div>', unsafe_allow_html=True)

# --- 6. 核心布局：双栏设计 ---
col_work, col_lib = st.columns([1, 1]) # 左侧操作，右侧库，比例 1:1

# =======================
# 右侧：固定资产库 (Library)
# =======================
with col_lib:
    st.subheader("📚 资产仓库")
    
    # 筛选工具栏
    f_col1, f_col2 = st.columns([2, 1])
    with f_col1:
        filter_cat = st.selectbox("分类", ["主体", "风格", "部位", "氛围"], label_visibility="collapsed")
    with f_col2:
        show_fav = st.checkbox("仅收藏 ⭐")

    # 显示区域
    st.markdown('<div class="chip-container">', unsafe_allow_html=True)
    
    current_list = st.session_state.db[filter_cat]
    if show_fav:
        current_list = [i for i in current_list if i in st.session_state.db["收藏"]]
    
    # 渲染每一个标签
    for item in current_list:
        is_fav = item in st.session_state.db["收藏"]
        border_color = "#ffd700" if is_fav else "#30363d"
        
        # 布局：标签名 + 收藏按钮 + 删除按钮
        c_tag, c_act = st.columns([4, 2])
        with c_tag:
            st.markdown(f'<span class="chip" style="border-color:{border_color}">{item}</span>', unsafe_allow_html=True)
        with c_act:
            # 收藏/取消收藏
            if st.button("⭐" if not is_fav else "★", key=f"fav_{item}", help="收藏"):
                if is_fav: st.session_state.db["收藏"].remove(item)
                else: st.session_state.db["收藏"].append(item)
                sync_github("favorites.txt", st.session_state.db["收藏"])
                st.rerun()
                
            # 删除
            if st.button("×", key=f"del_{item}", help="删除"):
                st.session_state.db[filter_cat].remove(item)
                file_map = {"主体": "subjects.txt", "风格": "styles.txt", "部位": "placements.txt", "氛围": "vibes.txt"}
                sync_github(file_map[filter_cat], st.session_state.db[filter_cat])
                st.rerun()
                
    st.markdown('</div>', unsafe_allow_html=True)


# =======================
# 左侧：动态操作区 (Workspace)
# =======================
with col_work:
    
    # --- 模式 A: 智能入库 ---
    if mode == "✨ 智能入库":
        st.subheader("📥 智能提取入库")
        
        # 1. 输入区
        input_text = st.text_area("输入描述", height=120, placeholder="例如：日式老传统风格，般若面具，配上樱花和流水，适合小腿...")
        
        # 2. 拆解按钮
        if st.button("🔍 开始拆解", type="primary", use_container_width=True):
            if input_text:
                with st.spinner("AI 正在分析..."):
                    prompt = "提取纹身元素。格式:分类:内容。分类限:主体,风格,部位,氛围。内容要短。"
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": input_text}]
                    ).choices[0].message.content
                    
                    # 解析并暂存到 preview_tags
                    st.session_state.preview_tags = []
                    for p in res.replace("\n","|").split("|"):
                        if ":" in p:
                            k, v = p.split(":", 1)
                            # 自动归类
                            cat = next((x for x in ["主体","风格","部位","氛围"] if x in k), None)
                            if cat:
                                st.session_state.preview_tags.append({"cat": cat, "val": v.strip()})
        
        # 3. 预览与选择区 (如果有拆解结果)
        if st.session_state.preview_tags:
            st.divider()
            st.write("📝 **请勾选需要入库的标签：**")
            
            # 使用 Streamlit 的 Pills 组件 (如果有) 或 Checkbox
            selected_indices = []
            
            # 简单的复选框列表
            for idx, tag in enumerate(st.session_state.preview_tags):
                is_checked = st.checkbox(f"【{tag['cat']}】 {tag['val']}", value=True, key=f"chk_{idx}")
                if is_checked:
                    selected_indices.append(tag)
            
            col_save, col_clear = st.columns(2)
            
            # 4. 确认入库
            with col_save:
                if st.button("💾 一键入库选中项", type="primary", use_container_width=True):
                    count = 0
                    file_map = {"主体": "subjects.txt", "风格": "styles.txt", "部位": "placements.txt", "氛围": "vibes.txt"}
                    
                    for item in selected_indices:
                        cat = item['cat']
                        val = item['val']
                        if val not in st.session_state.db[cat]:
                            st.session_state.db[cat].append(val)
                            sync_github(file_map[cat], st.session_state.db[cat])
                            count += 1
                    
                    st.success(f"成功入库 {count} 个新标签！")
                    st.session_state.preview_tags = [] # 清空预览
                    st.rerun()
            
            # 5. 清空
            with col_clear:
                if st.button("🗑️ 放弃", use_container_width=True):
                    st.session_state.preview_tags = []
                    st.rerun()

    # --- 模式 B: 生成提示词 ---
    elif mode == "🎲 生成提示词":
        st.subheader("🎨 提示词生成")
        
        # 1. 参考图上传 (视觉占位，目前仅作展示)
        st.file_uploader("参考图 (可选，辅助灵感)", type=["png", "jpg"], help="当前版本仅作参考，AI暂不读取图片内容")
        
        # 2. 额外要求
        extra_req = st.text_input("额外要求 (可选)", placeholder="例如：黑白线条，极简...")
        
        # 3. 数量滑块
        gen_count = st.slider("生成数量", 1, 5, 1)
        
        # 4. 生成按钮
        if st.button("🚀 立即生成", type="primary", use_container_width=True):
            if all(len(v) > 0 for v in [st.session_state.db["主体"], st.session_state.db["风格"]]):
                for i in range(gen_count):
                    # 随机抽取逻辑
                    s = random.choice(st.session_state.db["主体"])
                    sty = random.choice(st.session_state.db["风格"])
                    p = random.choice(st.session_state.db["部位"]) if st.session_state.db["部位"] else "Skin"
                    v = random.choice(st.session_state.db["氛围"]) if st.session_state.db["氛围"] else "Artistic"
                    
                    # 组合 Prompt
                    final_prompt = f"/imagine prompt: {s}, {sty} style, {v} vibe, on {p}"
                    if extra_req:
                        final_prompt += f", {extra_req}"
                    final_prompt += " --v 6.0 --ar 2:3"
                    
                    # 瀑布流卡片展示
                    st.markdown(f"""
                    <div class="prompt-card">
                        <div style="font-weight:bold; color:#4facfe; margin-bottom:5px;">#{i+1} 创意组合</div>
                        <div style="font-size:14px; color:#ddd;">{sty} · {s}</div>
                        <div style="background:#000; padding:8px; border-radius:6px; margin-top:8px; font-family:monospace; font-size:12px; color:#8b949e;">
                            {final_prompt}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("库存不足，请先去【智能入库】添加素材！")
