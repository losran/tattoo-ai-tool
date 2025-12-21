import streamlit as st
from openai import OpenAI
import random
import requests
import base64

# 安全读取密钥
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

st.set_page_config(page_title="Tattoo Studio Management", layout="wide")

# --- 增强版 CSS (支持分组样式) ---
st.markdown("""
    <style>
    .group-header {
        font-size: 12px;
        font-weight: 700;
        color: #86868b;
        text-transform: uppercase;
        margin: 15px 0 5px 5px;
        letter-spacing: 1px;
    }
    .asset-tag {
        display: inline-flex;
        align-items: center;
        background: rgba(0, 113, 227, 0.08);
        color: #0071e3 !important;
        padding: 4px 10px;
        border-radius: 8px;
        margin: 3px;
        font-size: 13px;
        border: 1px solid rgba(0, 113, 227, 0.1);
    }
    .delete-btn {
        margin-left: 6px;
        cursor: pointer;
        opacity: 0.5;
    }
    .delete-btn:hover { opacity: 1; color: #ff3b30; }
    </style>
""", unsafe_allow_html=True)

# --- 云端删除逻辑 ---
def delete_from_github(category, word_to_del):
    paths = {"主体": "data/subjects.txt", "风格": "data/styles.txt", "部位": "data/placements.txt", "氛围": "data/vibes.txt"}
    path = paths.get(category)
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    r = requests.get(url, headers=headers).json()
    if 'sha' in r:
        content = base64.b64decode(r['content']).decode('utf-8')
        # 过滤掉要删除的词
        lines = [l for l in content.split('\n') if l.strip() != word_to_del]
        new_txt = "\n".join(lines)
        payload = {
            "message": f"Delete {word_to_del}",
            "content": base64.b64encode(new_txt.encode('utf-8')).decode('utf-8'),
            "sha": r['sha']
        }
        requests.put(url, headers=headers, json=payload)
        st.cache_data.clear() # 清除缓存强制刷新

# --- 智能拆解：支持自动分组 ---
def handle_disassembly():
    val = st.session_state.temp_input
    if val:
        with st.spinner('AI 正在进行智能分组拆解...'):
            res = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": "你是一个纹身资产专家。请按 格式: 分类:【分组】/零件 拆解。例如 主体:【动物】/机械狮子。分类仅限:主体,风格,部位,氛围。"},
                          {"role": "user", "content": val}]
            ).choices[0].message.content
            # ... (同步逻辑与之前一致，支持存入带分组的字符串)
            st.session_state.temp_input = ""
            st.rerun()

# --- 主界面：资产库管理 ---
st.title("📂 纹身资产库管理")

# 模拟分组展示逻辑
cols = st.columns(4)
sections = ["主体", "风格", "部位", "氛围"]

for i, sec in enumerate(sections):
    with cols[i]:
        st.subheader(sec)
        # 假设我们从 GitHub 读取到了带分组的词，如 "【动物】/狮子"
        raw_items = ["【动物】/狮子", "【植物】/玫瑰", "【动物】/老鹰", "纯黑线条"] 
        
        # 自动逻辑：按【】里的内容进行分组排序
        groups = {}
        for item in raw_items:
            g = item.split('/')[0] if '/' in item else "未分组"
            name = item.split('/')[1] if '/' in item else item
            groups.setdefault(g, []).append(name)
        
        for g_name, g_items in groups.items():
            st.markdown(f"<div class='group-header'>{g_name}</div>", unsafe_allow_html=True)
            for item in g_items:
                # 每一个标签都像是一个小组件
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"<div class='asset-tag'>{item}</div>", unsafe_allow_html=True)
                with c2:
                    if st.button("×", key=f"del_{sec}_{item}"):
                        delete_from_github(sec, f"{g_name}/{item}" if g_name != "未分组" else item)
                        st.rerun()
