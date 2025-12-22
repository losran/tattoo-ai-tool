import streamlit as st
from openai import OpenAI
import random, requests, base64, time

# --- 1. 基础配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Pro", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 稳定版 CSS (修复消失问题) ---
st.markdown("""
    <style>
    /* 基础重置 */
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .main { background-color: #0d0d0d; color: #fff; }
    .block-container { padding-top: 0 !important; max-width: 100% !important; }

    /* [1] 左侧导航：绝对定位于左侧 */
    [data-testid="stColumn"]:nth-child(1) {
        background-color: #161b22;
        border-right: 1px solid #333;
        padding: 20px !important;
        height: 100vh;
        position: fixed; left: 0; top: 0; 
        width: 130px !important;
        z-index: 999;
    }
  
    /* [2] 中间操作区：自适应宽度 */
    [data-testid="stColumn"]:nth-child(2) {
        margin-left: 140px !important; /* 给左边留位置 */
        margin-right: 360px !important; /* 给右边留位置 */
        padding: 40px !important;
        width: auto !important;
    }

    /* [3] 右侧仓库：绝对定位于右侧 (修复消失bug) */
    [data-testid="stColumn"]:nth-child(3) {
        background-color: #0d1117;
        border-left: 1px solid #333;
        padding: 20px !important;
        height: 100vh;
        position: fixed; right: 0; top: 0;
        width: 350px !important;
        z-index: 999;
        overflow-y: auto !important; /* 强制滚动条 */
    }

    /* 组件样式优化 */
    .stat-box { margin-bottom: 15px; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 8px; text-align: center; }
    .stat-num { font-size: 18px; font-weight: bold; color: #58a6ff; }
    .stTextArea textarea { background: #1a1a1a; color: #fff; border: 1px solid #333; }
    
    /* 标签样式 */
    .repo-item {
        display: flex; justify-content: space-between; align-items: center;
        background: #1f1f1f; margin-bottom: 6px; padding: 6px 12px; border-radius: 6px; border: 1px solid #333;
    }
    .repo-text { font-size: 13px; color: #ddd; }

      /* 左下角看板锁死 */
    .sticky-stats {
        position: fixed;
        left: 15px;
        bottom: 30px;
        width: 90px;
        z-index: 1002; /* 确保在最上层 */
    }
    .nav-item {
        background: rgba(255, 255, 255, 0.05); /* 确保有背景色 */
        border: 1px solid #333;
        border-radius: 8px;
        padding: 8px;
        margin-top: 8px;
        text-align: center;
    }
    .nav-label { font-size: 11px; color: #888; }
    .nav-val { font-size: 18px; font-weight: bold; color: #58a6ff; }

    </style>
    
""", unsafe_allow_html=True)

# --- 3. 数据逻辑 ---
def sync_git(fn, data):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    hd = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(url, headers=hd).json()
        sha = r.get('sha')
        # 过滤空字符
        clean_data = [d for d in data if d and d.strip()]
        content = base64.b64encode("\n".join(list(set(clean_data))).encode()).decode()
        requests.put(url, headers=hd, json={"message": "sync", "content": content, "sha": sha})
    except: pass

def get_git(fn):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{fn}"
    r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    if r.status_code == 200:
        return [l.strip() for l in base64.b64decode(r.json()['content']).decode('utf-8').splitlines() if l.strip()]
    return []

if 'db' not in st.session_state:
    st.session_state.db = {k: get_git(v) for k, v in {"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt","收藏":"favorites.txt"}.items()}
if 'pre_tags' not in st.session_state: st.session_state.pre_tags = []
if 'input_id' not in st.session_state: st.session_state.input_id = 0

# --- 4. 稳固布局 ---
# 这里的比例只是占位，真正的宽度由上面的 CSS 控制
col_nav, col_mid, col_lib = st.columns([1, 4, 2])

# 👉 左侧：统计
# 👉 左：Logo 顶部，统计固定底部

with col_nav:
    st.markdown("### 🌀") 
    
    # 构建 HTML 字符串
    stats_html = '<div class="sticky-stats">'
    for k in ["主体", "风格", "部位", "氛围"]:
        # 获取数量，如果获取失败默认为空列表
        items = st.session_state.db.get(k, [])
        num = len(items)
        # 拼接 HTML
        stats_html += f'<div class="nav-item"><div class="nav-label">{k}</div><div class="nav-val">{num}</div></div>'
    stats_html += '</div>'
    
    # 渲染 HTML (注意：unsafe_allow_html=True 是必须的！)
    st.markdown(stats_html, unsafe_allow_html=True)
# (复制到这里结束)
    
# 👉 中间：操作
with col_mid:
    st.title("✨ 智能提取入库")
    
    # 输入框 (动态ID清空)
    user_input = st.text_area("输入样板提示词", height=150, placeholder="在此输入...", key=f"input_{st.session_state.input_id}")
    
    if st.button("🔍 开始 AI 拆分", type="primary"):
        if user_input:
            with st.spinner("AI 思考中..."):
                try:
                    # 强力 Prompt：要求 AI 必须按格式，否则不通过
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": "你是一个提取工具。请严格按此格式输出：主体:内容|风格:内容|部位:内容|氛围:内容。若无相关内容则跳过。不要说废话。"},
                            {"role": "user", "content": user_input}
                        ],
                        temperature=0.1
                    ).choices[0].message.content
                    
                    # 容错解析逻辑
                    parsed = []
                    # 将换行符也视为分隔符
                    parts = res.replace("\n", "|").split("|")
                    for p in parts:
                        # 兼容中文冒号和英文冒号
                        p = p.replace("：", ":")
                        if ":" in p:
                            k, v = p.split(":", 1)
                            clean_k = k.strip()
                            clean_v = v.strip()
                            # 模糊匹配分类
                            valid_cat = None
                            if "主体" in clean_k: valid_cat = "主体"
                            elif "风格" in clean_k: valid_cat = "风格"
                            elif "部位" in clean_k: valid_cat = "部位"
                            elif "氛围" in clean_k: valid_cat = "氛围"
                            
                            if valid_cat and clean_v:
                                parsed.append({"cat": valid_cat, "val": clean_v, "ok": True})
                    
                    if parsed:
                        st.session_state.pre_tags = parsed
                        st.session_state.input_id += 1 # 清空输入框
                        st.rerun()
                    else:
                        st.error(f"AI返回了内容，但无法识别格式。原始返回：{res}")
                        
                except Exception as e:
                    st.error(f"连接出错: {e}")

    # 预览与入库区域
# [请确保这段代码缩进在 with col_mid: 的内部]
    
    # 3. 结果预览与按钮组
 # 👉 以下所有内容必须在 with col_mid: 内部，请确保前面有 4 或 8 个空格
    if st.session_state.pre_tags:
        st.markdown("---")
        st.subheader("确认拆解结果")
        
        save_list = []
        for i, tag in enumerate(st.session_state.pre_tags):
            if st.checkbox(f"【{tag['cat']}】{tag['val']}", value=True, key=f"chk_{i}"):
                save_list.append(tag)
        
        st.write("")
        
        # ⚠️ 关键点：这两行前面必须有缩进！
         c_btn_a, c_btn_b = st.columns([1, 2]) 
        
        with c_btn_a:
            # 放弃按钮：现在它属于 c_btn_a，c_btn_a 又属于 col_mid
            if st.button("🧹 放弃", use_container_width=True):
                st.session_state.pre_tags = []
                st.rerun()
                
        with c_btn_b:
            # 入库按钮
            if st.button("🚀 一键入云库", type="primary", use_container_width=True):
                # ... (此处省略同步逻辑代码)
                st.rerun()
                
# 👉 右侧：资产库 (使用原生组件确保可见性)
with col_lib:
    st.subheader("📚 资产仓库")
    
    # 顶部工具
    view_cat = st.selectbox("分类", ["主体", "风格", "部位", "氛围"], label_visibility="collapsed")
    
    st.divider()
    
    # 强制文字颜色为白色，防止不可见
    st.markdown('<div style="color:white">', unsafe_allow_html=True)
    
    items = st.session_state.db.get(view_cat, [])
    
    # 调试信息：如果列表为空但统计有数，说明读取有问题
    if not items and len(st.session_state.db.get(view_cat, [])) > 0:
         # 强制重新加载一次
         st.session_state.db[view_cat] = get_git({"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}[view_cat])
         items = st.session_state.db[view_cat]

    if items:
        for word in items:
            # 手动布局每一行
            c_txt, c_act = st.columns([7, 2])
            with c_txt:
                st.markdown(f'<div class="repo-item"><span class="repo-text">{word}</span></div>', unsafe_allow_html=True)
            with c_act:
                 if st.button("🗑️", key=f"del_{word}"):
                    st.session_state.db[view_cat].remove(word)
                    sync_git({"主体":"subjects.txt","风格":"styles.txt","部位":"placements.txt","氛围":"vibes.txt"}[view_cat], st.session_state.db[view_cat])
                    st.rerun()
    else:
        st.info("暂无数据")
    
    st.markdown('</div>', unsafe_allow_html=True)






