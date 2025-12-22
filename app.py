import streamlit as st
from openai import OpenAI
import requests, base64, time

# --- 1. 极简配置区 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"
# 定义五个核心维度与其对应的文件名
FILES = {
    "Subject": "subjects.txt", "Action": "actions.txt", 
    "Style": "styles.txt", "Mood": "moods.txt", "Usage": "usage.txt"
}

st.set_page_config(layout="wide", page_title="Tattoo Lite")

# --- 2. 只有必要的 CSS (去头去尾，让空间更大) ---
st.markdown("""
    <style>
    header, [data-testid="stHeader"] {visibility: hidden;}
    .block-container {padding-top: 20px; padding-bottom: 20px;}
    /* 简单的统计卡片样式 */
    .stat-card {border:1px solid #333; border-radius:5px; padding:10px; margin-bottom:5px; text-align:center; background:#111;}
    .stat-num {font-size:18px; color:#4CAF50; font-weight:bold;}
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心工具函数 (压缩版) ---
def get_data(filename):
    """从 GitHub 获取数据列表"""
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return [line.strip() for line in base64.b64decode(resp.json()['content']).decode().splitlines() if line.strip()]
    return []

def sync_data(filename, data_list):
    """同步数据回 GitHub"""
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    # 先获取当前的 SHA
    get_resp = requests.get(url, headers=headers).json()
    # 编码内容
    content_str = "\n".join(sorted(list(set(data_list)))) # 自动去重排序
    b64_content = base64.b64encode(content_str.encode()).decode()
    # 推送更新
    requests.put(url, headers=headers, json={
        "message": "update from lite tool",
        "content": b64_content,
        "sha": get_resp.get('sha')
    })

# --- 4. 初始化状态 ---
if 'db' not in st.session_state:
    st.session_state.db = {k: get_data(v) for k, v in FILES.items()}
if 'results' not in st.session_state:
    st.session_state.results = []

# --- 5. 页面布局 (左-中-右) ---
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
    txt = st.text_area("输入文案", height=100, placeholder="在此粘贴...")
    
    if st.button("💥 拆解", type="primary", use_container_width=True):
        if txt:
            # AI 调用
            prompt = f"把这段话拆解为 Subject, Action, Style, Mood, Usage 五类。格式：类别:词|类别:词。原文：{txt}"
            res = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            ).choices[0].message.content
            
            # 极简清洗逻辑
            parsed = []
            clean = res.replace("**", "").replace("\n", "|").replace("：", ":")
            for item in clean.split("|"):
                if ":" in item:
                    cat, val = item.split(":", 1)
                    # 模糊匹配类别
                    for key in FILES.keys():
                        if key.lower() in cat.lower():
                            # 拆分逗号顿号
                            for w in val.replace("、", "/").replace(",", "/").split("/"):
                                if w.strip(): parsed.append({"cat": key, "val": w.strip()})
            st.session_state.results = parsed
            st.rerun()

    # 结果预览区
    if st.session_state.results:
        st.divider()
        st.caption("勾选以入库：")
        
        # 收集用户勾选的词
        selected = []
        # 按分类简单的展示出来，不再强求花哨布局
        for cat in FILES.keys():
            items = [x for x in st.session_state.results if x['cat'] == cat]
            if items:
                st.markdown(f"**{cat}**")
                cols = st.columns(4) # 简单的物理四列，最稳妥
                for i, item in enumerate(items):
                    with cols[i % 4]:
                        if st.checkbox(item['val'], value=True, key=f"chk_{item['val']}_{i}"):
                            selected.append(item)
        
        st.write("")
        c1, c2 = st.columns(2)
        if c1.button("🚀 存入云端", type="primary", use_container_width=True):
            # 批量入库逻辑
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

# 👉 右栏：仓库管理
with c_lib:
    st.subheader("📦 仓库")
    cat_view = st.selectbox("查看分类", list(FILES.keys()))
    
    current_list = st.session_state.db[cat_view]
    to_delete = []
    
    if current_list:
        with st.container(height=600): # 这一招能让右边自己滚动，不影响整体
            for item in current_list:
                if st.checkbox(item, key=f"del_{item}"):
                    to_delete.append(item)
        
        if to_delete:
            if st.button(f"删除选中 ({len(to_delete)})", type="secondary"):
                # 执行删除
                new_list = [x for x in current_list if x not in to_delete]
                st.session_state.db[cat_view] = new_list
                sync_data(FILES[cat_view], new_list)
                st.rerun()
    else:
        st.caption("空空如也")
