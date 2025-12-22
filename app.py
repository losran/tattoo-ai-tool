import streamlit as st
import requests, base64, time
from openai import OpenAI

# --- 1. 核心配置必须放第一行 (修复报错关键) ---
st.set_page_config(layout="wide", page_title="Tattoo Lite")

# --- 2. 样式定义 (直接集成，不再依赖外部文件) ---
st.markdown("""
<style>
    /* 1. 整体暗色基调 */
    .stApp {
        background-color: #0e1117;
        font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
    }

    /* 2. 隐藏顶部多余元素，让空间更大 */
    header, [data-testid="stHeader"] {visibility: hidden;}
    .block-container {padding-top: 20px; padding-bottom: 20px;}

    /* 3. 核心输入框 - 磨砂黑质感 */
    .stTextArea textarea {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        border-radius: 12px !important;
        color: #c9d1d9 !important;
    }
    .stTextArea textarea:focus {
        border-color: #ff4b4b !important;
        box-shadow: 0 0 0 1px #ff4b4b !important;
    }

    /* 4. 拆分出的“小标签”样式 */
    div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] > button {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 20px !important;
        padding: 4px 15px !important;
        font-size: 13px !important;
        color: #8b949e !important;
    }
    
    /* 5. 底部大按钮 - 一键入库 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ff4b4b 0%, #d62f2f 100%) !important;
        border: none !important;
        height: 45px !important;
        border-radius: 8px !important;
    }

    /* 6. 简单的左侧统计卡片样式 */
    .stat-card {
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 8px;
        text-align: center;
        background: #161b22;
    }
    .stat-num { font-size: 18px; color: #4CAF50; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 3. 初始化配置 ---
# ⚠️ 确保 .streamlit/secrets.toml 里有 DEEPSEEK_KEY 和 GITHUB_TOKEN
try:
    client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
except Exception as e:
    st.error("⚠️ 请检查 secrets.toml 配置！")
    st.stop()

REPO = "losran/tattoo-ai-tool"
FILES = {
    "Subject": "subjects.txt", "Action": "actions.txt", 
    "Style": "styles.txt", "Mood": "moods.txt", "Usage": "usage.txt"
}

# --- 4. 核心工具函数 ---
def get_data(filename):
    """从 GitHub 获取数据列表"""
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return [line.strip() for line in base64.b64decode(resp.json()['content']).decode().splitlines() if line.strip()]
    except:
        pass
    return []

def sync_data(filename, data_list):
    """同步数据回 GitHub"""
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        get_resp = requests.get(url, headers=headers).json()
        content_str = "\n".join(sorted(list(set(data_list))))
        b64_content = base64.b64encode(content_str.encode()).decode()
        requests.put(url, headers=headers, json={
            "message": "update from lite tool",
            "content": b64_content,
            "sha": get_resp.get('sha')
        })
    except Exception as e:
        st.error(f"同步失败: {e}")

# --- 5. 初始化状态 ---
if 'db' not in st.session_state:
    st.session_state.db = {k: get_data(v) for k, v in FILES.items()}
if 'results' not in st.session_state:
    st.session_state.results = []

# --- 6. 页面布局 (左-中-右) ---
c_nav, c_main, c_lib = st.columns([1, 4, 2])

# 👉 左栏：统计
with c_nav:
    st.markdown("### 📊")
    for k, v in st.session_state.db.items():
        st.markdown(f"""
        <div class="stat-card">
            <div style="color:#888;font-size:12px">{k}</div>
            <div class="stat-num">{len(v)}</div>
        </div>
        """, unsafe_allow_html=True)

# 👉 中栏：操作核心
with c_main:
    st.title("⚡ 极简纹身工作台")
    txt = st.text_area("输入文案", height=100, placeholder="在此粘贴客户需求...")
    
    if st.button("💥 拆解", type="primary", use_container_width=True):
        if txt:
            prompt = f"""
            你是一个纹身视觉元素提取器。请从下文中提取具体的画面细节，填入五维模型：
            1. Subject: 必须提取具体的物体名词（如：雏菊、蛇、几何体、月亮）。
            2. Action: 具体的动态（如：缠绕、绽放、流淌）。
            3. Style: 视觉风格（如：水彩、线条、Old School）。
            4. Mood: 氛围关键词。
            5. Usage: 部位或用途。
            
            原文：{txt}
            
            输出格式要求：Subject:雏菊|Action:绽放|Style:水彩... (用|分隔，不要加序号)
            """
            
            with st.spinner("🔍 正在狠抠细节..."):
                try:
                    res = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1
                    ).choices[0].message.content
                    
                    # 解析逻辑
                    parsed = []
                    clean = res.replace("**", "").replace("\n", "|").replace("：", ":").replace("  ", "")
                    
                    for item in clean.split("|"):
                        if ":" in item:
                            cat, val = item.split(":", 1)
                            for key in FILES.keys():
                                if key.lower() in cat.lower():
                                    for w in val.replace("、", "/").replace(",", "/").replace("，", "/").split("/"):
                                        w = w.strip()
                                        if w and w not in ["无", "未提及", "N/A"]: 
                                            parsed.append({"cat": key, "val": w})
                    
                    st.session_state.results = parsed
                    st.rerun()
                except Exception as e:
                    st.error(f"AI 请求失败: {e}")

    # 结果预览与入库区
    if st.session_state.results:
        st.divider()
        st.caption("勾选以入库：")
        
        selected = []
        for cat in FILES.keys():
            items = [x for x in st.session_state.results if x['cat'] == cat]
            if items:
                st.markdown(f"**{cat}**")
                cols = st.columns(4)
                for i, item in enumerate(items):
                    with cols[i % 4]:
                        if st.checkbox(item['val'], value=True, key=f"chk_{item['val']}_{i}"):
                            selected.append(item)
        
        st.write("")
        c1, c2 = st.columns(2)
        if c1.button("🚀 存入云端", type="primary", use_container_width=True):
            for item in selected:
                cat = item['cat']
                if item['val'] not in st.session_state.db[cat]:
                    st.session_state.db[cat].append(item['val'])
                    # 实时同步
                    sync_data(FILES[cat], st.session_state.db[cat])
            st.session_state.results = []
            st.success("已保存！")
            time.sleep(1)
            st.rerun()
            
        if c2.button("清空", use_container_width=True):
            st.session_state.results = []
            st.rerun()

# 👉 右栏：仓库管理 (带滚动条，不占用主屏)
with c_lib:
    st.subheader("📦 仓库")
    cat_view = st.selectbox("查看分类", list(FILES.keys()))
    
    current_list = st.session_state.db.get(cat_view, [])
    to_delete = []
    
    if current_list:
        # 使用容器限制高度，让列表在右侧内部滚动
        with st.container(height=600):
            for item in current_list:
                if st.checkbox(item, key=f"del_{item}"):
                    to_delete.append(item)
        
        if to_delete:
            if st.button(f"删除选中 ({len(to_delete)})"):
                new_list = [x for x in current_list if x not in to_delete]
                st.session_state.db[cat_view] = new_list
                sync_data(FILES[cat_view], new_list)
                st.rerun()
    else:
        st.caption("空空如也")
