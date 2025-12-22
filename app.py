import streamlit as st
from openai import OpenAI
import random, requests, base64, time

# --- 1. 基础配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Pro Station", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 核心 CSS 布局 (强制隔离三栏 + 碎片卡片化) ---
st.markdown("""
    <style>
    /* 基础清理：隐藏页眉页脚，让空间更大 */
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .main { background-color: #0d0d0d; color: #fff; }
    .block-container { padding: 0 !important; max-width: 100% !important; }

    /* [左] 固定看板：宽度锁死在 120px */
    [data-testid="stColumn"]:nth-child(1) {
        position: fixed; left: 0; top: 0; bottom: 0; width: 120px !important;
        background: #161b22; border-right: 1px solid #333; z-index: 1001; padding-top: 20px !important;
    }
    .sticky-stats { position: fixed; left: 10px; bottom: 20px; width: 100px; z-index: 1002; }
    .nav-item { background: rgba(255,255,255,0.05); border: 1px solid #333; border-radius: 8px; padding: 8px; margin-top: 8px; text-align: center; }
    .nav-val { color: #58a6ff; font-weight: bold; font-size: 16px; }

    /* [中] 生产区：自适应宽度，左右留出物理边距 */
    [data-testid="stColumn"]:nth-child(2) {
        margin-left: 140px !important; margin-right: 380px !important;
        width: auto !important; padding: 40px !important; min-height: 100vh;
    }

    /* [右] 仓库区：宽度锁死在 360px，独立滚动 */
    [data-testid="stColumn"]:nth-child(3) {
        position: fixed; right: 0; top: 0; bottom: 0; width: 360px !important;
        background: #0d1117; border-left: 1px solid #333; padding: 30px 20px !important;
        z-index: 1000; overflow-y: auto !important;
    }

    /* 💥 碎片卡片样式 (带边框的大爆炸方块) */
    [data-testid="stCheckbox"] {
        background: #1f2428 !important; border: 1px solid #333 !important;
        padding: 5px 10px !important; border-radius: 6px !important; margin-bottom: 5px !important;
    }
    /* 勾选后的高亮红色效果 */
    [data-testid="stCheckbox"]:has(input:checked) {
        border-color: #ff4b4b !important; background: #2d1b1b !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. 数据读写函数 (带清理逻辑) ---
def sync_git(fn, data):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    hd = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(url, headers=hd).json()
        clean_data = [d.strip() for d in data if d and d.strip()] # 去除空行
        content = base64.b64encode("\n".join(list(set(clean_data))).encode()).decode()
        requests.put(url, headers=hd, json={"message": "sync", "content": content, "sha": r.get('sha')})
    except: pass

def get_git(fn):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if r.status_code == 200:
        return [l.strip() for l in base64.b64decode(r.json()['content']).decode('utf-8').splitlines() if l.strip()]
    return []

# 初始化 session_state
if 'db' not in st.session_state:
    st.session_state.db = {k: get_git(v) for k, v in {
        "Subject":"subjects.txt", "Action":"actions.txt", 
        "Style":"styles.txt", "Mood":"moods.txt", "Usage":"usage.txt"
    }.items()}
if 'pre_tags' not in st.session_state: st.session_state.pre_tags = []
if 'input_id' not in st.session_state: st.session_state.input_id = 0# --- 4. 物理分栏布局渲染 ---
# 这里的比例 [12, 53, 35] 对应了 CSS 中定义的固定宽度比例
col_nav, col_mid, col_lib = st.columns([12, 53, 35])

# 👉 [左侧栏] 资产统计看板
with col_nav:
    # 顶部小图标，增加呼吸感
    st.markdown("### 🌀") 
    
    # 构造看板 HTML
    # 注意：这里展示你最关心的 4 个核心维度统计
    stats_html = '<div class="sticky-stats">'
    for k in ["Subject", "Style", "Action", "Mood"]:
        num = len(st.session_state.db.get(k, []))
        stats_html += f'''
            <div class="nav-item">
                <div style="font-size:10px;color:#888">{k}</div>
                <div class="nav-val">{num}</div>
            </div>
        '''
    st.markdown(stats_html + '</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 下面开始进入中间生产区，我们先打个招呼，确认位置正确
with col_mid:
    st.title("✨ 灵感大爆炸拆解")
    st.caption("基于五维模型：Subject | Action | Style | Mood | Usage")# 1. 动态输入框：使用 input_id 确保入库后自动清空
    raw_input = st.text_area(
        "粘贴样板描述词", 
        height=150, 
        key=f"in_{st.session_state.input_id}", 
        placeholder="例如：水彩纹身，淡绿色薄荷枝条，随风摇曳，清冷氛围..."
    )
    
    # 2. 🔍 执行拆解按钮
    if st.button("🔍 立即炸开碎片", type="primary", use_container_width=True):
        if raw_input:
            with st.spinner("💥 正在执行五维深度拆解..."):
                try:
                    # 向 DeepSeek 发起指令
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": """你是一个专业的纹身提示词拆解专家。
                            请将文案打碎并归类到以下五个维度：
                            1. Subject (核心主体/名词)
                            2. Action (动作/姿态/具体状态)
                            3. Style (视觉风格/技法)
                            4. Mood (情绪/氛围感)
                            5. Usage (使用场景/建议)
                            输出格式：类别:词|类别:词。禁止废话，词要拆得极细。"""},
                            {"role": "user", "content": raw_input}
                        ],
                        temperature=0.1 # 极低随机性，确保输出稳定
                    ).choices[0].message.content
                    
                    # --- [TEST: 解析与清洗逻辑] ---
                    parsed_results = []
                    # 剥除加粗、统一符号、处理换行
                    clean_res = res.replace("**", "").replace("：", ":").replace("\n", "|")
                    
                    for part in clean_res.split("|"):
                        if ":" in part:
                            k, v = part.split(":", 1)
                            # 模糊匹配五大分类名
                            found_cat = None
                            for target in ["Subject", "Action", "Style", "Mood", "Usage"]:
                                if target.lower() in k.lower():
                                    found_cat = target
                                    break
                            
                            if found_cat:
                                # 极细粒度打碎：处理逗号、顿号、空格、斜杠
                                sub_words = v.replace("、", "/").replace(",", "/").replace(" ", "/").replace("，", "/").split("/")
                                for sw in sub_words:
                                    if sw.strip():
                                        parsed_results.append({"cat": found_cat, "val": sw.strip()})
                    
                    # 存入 session 状态并强制重绘页面
                    if parsed_results:
                        st.session_state.pre_tags = parsed_results
                        st.session_state.input_id += 1 # 触发输入框清空
                        st.rerun() 
                    else:
                        st.error(f"❌ 诊断失败：AI未按格式返回。原文：{res}")
                        
                except Exception as e:
                    st.error(f"📡 网络或接口异常: {e}")# 3. 🏁 碎片预览区 (只有当 pre_tags 有数据时才显示)
    if st.session_state.pre_tags:
        st.write("---")
        st.subheader("📋 碎片预览 (勾选想要入库的)")
        
        # 用于存放用户最终勾选的碎片
        save_list = []
        
        # 定义五维展示顺序
        order = ["Subject", "Action", "Style", "Mood", "Usage"]
        
        for display_cat in order:
            # 过滤出当前分类下的词条
            words = [t for t in st.session_state.pre_tags if t['cat'] == display_cat]
            if words:
                st.markdown(f"**📍 {display_cat}**")
                # 创建 3 列布局，让碎片横向炸开
                cols = st.columns(3)
                for i, w in enumerate(words):
                    with cols[i % 3]:
                        # 核心交互：每个词都是一个独立的带边框 Checkbox
                        # key 中加入 input_id 确保每次拆解都是全新的组件 ID
                        k_id = f"pre_{display_cat}_{i}_{st.session_state.input_id}"
                        if st.checkbox(w['val'], value=True, key=k_id):
                            save_list.append(w)
        
        # 4. 预览区操作按钮组
        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 一键入云库", type="primary", use_container_width=True):
                # 建立维度与 GitHub 文件名的映射
                f_map = {
                    "Subject": "subjects.txt",
                    "Action": "actions.txt",
                    "Style": "styles.txt",
                    "Mood": "moods.txt",
                    "Usage": "usage.txt"
                }
                
                # 遍历勾选的碎片，去重并存入数据库
                for t in save_list:
                    cat_key = t['cat']
                    val = t['val']
                    if val not in st.session_state.db.get(cat_key, []):
                        st.session_state.db.setdefault(cat_key, []).append(val)
                        # 调用 GitHub 同步函数
                        sync_git(f_map.get(cat_key, "misc.txt"), st.session_state.db[cat_key])
                
                # 入库完成后，清空预览区并刷新页面
                st.session_state.pre_tags = []
                st.success("🎉 已成功存入云端仓库！")
                time.sleep(0.8)
                st.rerun()
        
        with c2:
            if st.button("🧹 扫走碎片 (清空)", use_container_width=True):
                st.session_state.pre_tags = []
                st.rerun()# 👉 [右侧栏] 资产管理仓库 (带边框碎片化展示)
with col_lib:
    st.subheader("📚 仓库整理")
    
    # 1. 顶部切换分类：直接查看五个维度的数据
    manage_cat = st.selectbox(
        "选择维度", 
        ["Subject", "Action", "Style", "Mood", "Usage"], 
        key="lib_cat_selector", 
        label_visibility="collapsed"
    )
    st.divider()

    # 2. 获取该维度下的词条列表
    all_items = st.session_state.db.get(manage_cat, [])
    
    if all_items:
        st.caption(f"当前共 {len(all_items)} 个碎片，勾选执行批量删除：")
        
        # 记录选中的删除项
        delete_list = []
        
        # 3. 碎片展示：使用 2 列布局适配较窄的右边栏
        lib_cols = st.columns(2)
        for i, item in enumerate(all_items):
            with lib_cols[i % 2]:
                # 每个词条都是一个带边框的选择块
                # 默认不勾选，勾选代表“选中待删”
                if st.checkbox(item, value=False, key=f"lib_del_{manage_cat}_{i}"):
                    delete_list.append(item)
        
        # 4. 删除执行按钮
        if delete_list:
            st.write("")
            if st.button(f"🗑️ 批量清理 {len(delete_list)} 个碎片", type="secondary", use_container_width=True):
                # 过滤掉被选中的词
                new_items = [x for x in all_items if x not in delete_list]
                st.session_state.db[manage_cat] = new_items
                
                # 同步更新 GitHub 上的 .txt 文件
                f_map = {
                    "Subject": "subjects.txt",
                    "Action": "actions.txt",
                    "Style": "styles.txt",
                    "Mood": "moods.txt",
                    "Usage": "usage.txt"
                }
                sync_git(f_map[manage_cat], new_items)
                
                st.success("✨ 仓库清理完毕！")
                time.sleep(0.5)
                st.rerun()
    else:
        st.info("💡 该分类下暂无素材，快去中间拆解一些吧！")

