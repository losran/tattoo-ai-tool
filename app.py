import streamlit as st
from openai import OpenAI
import random, requests, base64, time

# --- 1. 配置与初始化 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Pro Station", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 核心 CSS (还原设计稿：三栏固定 + 高亮标签) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d0d0d; color: #ffffff; }
    /* 三栏物理分割 */
    [data-testid="stColumn"]:nth-child(1) { position: fixed; left: 0; top: 0; bottom: 0; width: 80px !important; background: #1a1a1a; border-right: 1px solid #2d2d2d; padding: 20px 0 !important; z-index: 1001; }
    [data-testid="stColumn"]:nth-child(2) { margin-left: 100px !important; width: 45% !important; padding: 40px !important; }
    [data-testid="stColumn"]:nth-child(3) { position: fixed; right: 0; top: 0; bottom: 0; width: 38% !important; background: #0d0d0d; border-left: 1px solid #2d2d2d; padding: 30px !important; z-index: 1000; overflow-y: auto; }
    
    /* 交互式标签样式 */
    .preview-chip { display: inline-flex; align-items: center; padding: 6px 15px; border-radius: 8px; margin: 5px; cursor: pointer; border: 1px solid #444; background: #1a1a1a; transition: 0.2s; }
    .chip-selected { background: #0071e3 !important; border-color: #0071e3 !important; color: white !important; font-weight: bold; }
    .lib-chip { display: inline-flex; align-items: center; background: #1f1f1f; border: 1px solid #333; color: #58a6ff; padding: 3px 10px; border-radius: 6px; font-size: 13px; margin: 3px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 数据读写补丁 ---
def sync_git(fn, data):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    hd = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r_get = requests.get(url, headers=hd).json()
    sha = r_get.get('sha')
    content = base64.b64encode("\n".join(list(set(data))).encode()).decode()
    requests.put(url, headers=hd, json={"message": "sync", "content": content, "sha": sha})

if 'db' not in st.session_state:
    files = {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt","收藏":"favorites.txt"}
    st.session_state.db = {k: [] for k in files}
    # (此处应有初始化从GitHub读取逻辑，参考之前代码)

# 初始化中间操作区的状态
if 'is_split' not in st.session_state: st.session_state.is_split = False
if 'tags_to_save' not in st.session_state: st.session_state.tags_to_save = []

# --- 4. 物理布局构建 ---
col_nav, col_mid, col_lib = st.columns([8, 45, 38])

# 👉 左：极窄导航
with col_nav:
    st.markdown("🌀", help="Tattoo AI Logo")
    st.caption(f"主体\n{len(st.session_state.db['主体'])}")
    st.caption(f"风格\n{len(st.session_state.db['风格'])}")

# 👉 中：流式生产区 (Workspace)
with col_mid:
    st.title("✨ 智能入库")
    
    # 输入框：始终保留
    user_input = st.text_area("输入样板提示词", height=150, placeholder="描述文本...", key="main_input_box")
    
    # 动态按钮逻辑
    if not st.session_state.is_split:
        # 初始状态：显示“开始拆分”
        if st.button("🔍 开始 AI 拆分", type="primary", use_container_width=True):
            if user_input:
                progress_bar = st.progress(0)
                for percent_complete in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(percent_complete + 1)
                
                # AI 处理
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": "格式:分类:词|分类:词。分类限:主体,风格,部位,氛围。"}, {"role": "user", "content": user_input}]
                ).choices[0].message.content
                
                # 先保存在本地 Session
                st.session_state.tags_to_save = [{"cat": p.split(":")[0], "val": p.split(":")[1], "selected": True} for p in res.split("|") if ":" in p]
                st.session_state.is_split = True
                st.rerun()
    else:
        # 拆分后状态：显示 AI 预览结果（高亮选择）
        st.markdown("### AI 拆解预览 (请点击标签进行筛选)")
        
        # 渲染可交互的标签预览
        for i, tag in enumerate(st.session_state.tags_to_save):
            # 使用简单的 checkbox 模拟高亮选择视觉
            is_selected = st.checkbox(f"【{tag['cat']}】{tag['val']}", value=tag['selected'], key=f"preview_{i}")
            st.session_state.tags_to_save[i]['selected'] = is_selected

        col_a1, col_a2 = st.columns(2)
        with col_a1:
            if st.button("🚀 一键入云库", type="primary", use_container_width=True):
                f_map = {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}
                for t in st.session_state.tags_to_save:
                    if t['selected'] and t['val'] not in st.session_state.db[t['cat']]:
                        st.session_state.db[t['cat']].append(t['val'])
                        sync_git(f_map[t['cat']], st.session_state.db[t['cat']])
                st.session_state.is_split = False
                st.session_state.tags_to_save = []
                st.success("资产已同步至云端！")
                st.rerun()
        with col_a2:
            if st.button("🧹 重置并清空", use_container_width=True):
                st.session_state.is_split = False
                st.session_state.tags_to_save = []
                st.rerun()

# 👉 右：资产管理仓库
with col_lib:
    st.subheader("📚 资产管理仓库")
    
    # 下拉栏切换分类方式
    view_cat = st.selectbox("当前查看分类：", ["主体", "风格", "部位", "氛围"], index=0)
    
    st.divider()
    
    # 可视化管理：所有单词拆分成小标签
    items = st.session_state.db[view_cat]
    if items:
        for word in items:
            c1, c2, c3 = st.columns([6, 1, 1])
            with c1:
                st.markdown(f'<div class="lib-chip">{word}</div>', unsafe_allow_html=True)
            with c2:
                # 收藏逻辑
                is_fav = word in st.session_state.db["收藏"]
                if st.button("⭐" if is_fav else "🤍", key=f"f_{word}"):
                    if is_fav: st.session_state.db["收藏"].remove(word)
                    else: st.session_state.db["收藏"].append(word)
                    sync_git("favorites.txt", st.session_state.db["收藏"])
                    st.rerun()
            with c3:
                # 删除逻辑
                if st.button("🗑️", key=f"d_{word}"):
                    st.session_state.db[view_cat].remove(word)
                    f_name = {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}[view_cat]
                    sync_git(f_name, st.session_state.db[view_cat])
                    st.rerun()
    else:
        st.caption("该分类下暂无资产。")
