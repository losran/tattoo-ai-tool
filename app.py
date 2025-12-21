import streamlit as st
from openai import OpenAI
import random
import requests
import base64

# 1. 配置密钥 (从 Secrets 读取)
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

# 页面配置：适配 WAP 端
st.set_page_config(page_title="Tattoo Studio Pro", layout="wide", initial_sidebar_state="collapsed")

# --- 2. 视觉样式 (Figma 风格胶囊 + 分组) ---
st.markdown("""
    <style>
    /* 胶囊样式 */
    .chip-box {
        display: inline-flex;
        align-items: center;
        background: rgba(0, 113, 227, 0.08);
        color: #0071e3 !important;
        padding: 2px 8px;
        border-radius: 100px;
        font-size: 13px;
        margin: 3px;
        border: 1px solid rgba(0, 113, 227, 0.1);
    }
    .group-name {
        font-size: 11px;
        font-weight: 700;
        color: #86868b;
        margin: 12px 0 4px 5px;
        text-transform: uppercase;
    }
    /* 结果卡片 */
    .res-card {
        background: rgba(128, 128, 128, 0.05);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.1);
        margin-bottom: 12px;
    }
    /* 移动端适配 */
    @media (max-width: 640px) { .stColumn { width: 100% !important; } }
    </style>
""", unsafe_allow_html=True)

# --- 3. 核心逻辑：云端同步 ---
def github_action(category, content_list, action="update"):
    paths = {"主体": "data/subjects.txt", "风格": "data/styles.txt", "部位": "data/placements.txt", "氛围": "data/vibes.txt"}
    url = f"https://api.github.com/repos/{REPO}/contents/{paths[category]}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers).json()
    if 'sha' in r:
        new_txt = "\n".join(content_list)
        payload = {
            "message": f"{action} {category}",
            "content": base64.b64encode(new_txt.encode('utf-8')).decode('utf-8'),
            "sha": r['sha']
        }
        requests.put(url, headers=headers, json=payload)

# --- 4. 初始化数据 ---
if 'db' not in st.session_state:
    st.session_state.db = {"主体": [], "风格": [], "部位": [], "氛围": []}
    # 提示：实际使用时可在此处加入 requests.get 初始化读取 GitHub 文件

# --- 5. 侧边栏：提取入库 (保持自动清空) ---
with st.sidebar:
    st.header("📥 智能提取入库")
    # 使用 key 绑定实现自动清空
    if "input_val" not in st.session_state: st.session_state.input_val = ""
    
    user_input = st.text_area("粘贴样板描述", value=st.session_state.input_val, height=150, key="current_input")
    
    if st.button("开始拆解入库", type="primary", use_container_width=True):
        if st.session_state.current_input:
            with st.spinner('AI 正在智能分组并存入云端...'):
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": "按格式拆解: 分类:【分组】/零件。分类仅限:主体,风格,部位,氛围。"},
                              {"role": "user", "content": st.session_state.current_input}]
                ).choices[0].message.content
                
                for item in res.split("|"):
                    if ":" in item:
                        k, v = item.split(":", 1)
                        for sec in st.session_state.db.keys():
                            if sec in k:
                                word = v.strip()
                                if word not in st.session_state.db[sec]:
                                    st.session_state.db[sec].append(word)
                                    github_action(sec, st.session_state.db[sec])
                
                st.session_state.input_val = "" # 触发清空
                st.success("入库成功！输入框已重置。")
                st.rerun()

# --- 6. 主界面：看板展示 (带分组删除) ---
st.title("🎨 纹身设计资产看板")

cols = st.columns(4)
sections = ["主体", "风格", "部位", "氛围"]

for i, sec in enumerate(sections):
    with cols[i]:
        st.markdown(f"### {sec}")
        # 自动分组逻辑
        items = st.session_state.db[sec]
        grouped = {}
        for it in items:
            g = it.split('/')[0] if '/' in it else "未分组"
            name = it.split('/')[1] if '/' in it else it
            grouped.setdefault(g, []).append(name)
            
        for g_name, g_items in grouped.items():
            st.markdown(f"<div class='group-name'>{g_name}</div>", unsafe_allow_html=True)
            for item in g_items:
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"<div class='chip-box'>{item}</div>", unsafe_allow_html=True)
                with c2:
                    if st.button("×", key=f"del_{sec}_{item}_{random.random()}"):
                        full_name = f"{g_name}/{item}" if g_name != "未分组" else item
                        st.session_state.db[sec].remove(full_name)
                        github_action(sec, st.session_state.db[sec], "delete")
                        st.rerun()

st.markdown("<br><hr>", unsafe_allow_html=True)

# --- 7. 底部：灵感批量生成 ---
st.header("🎲 灵感批量生成")
gen_count = st.select_slider("选择生成数量", options=[1, 3, 5, 10], value=3)

if st.button("✨ 立即生成创意组合", use_container_width=True):
    db = st.session_state.db
    if all(len(v) > 0 for v in db.values()):
        st.balloons()
        res_cols = st.columns(2)
        for i in range(gen_count):
            # 随机抽卡
            s_raw = random.choice(db["主体"])
            sty_raw = random.choice(db["风格"])
            p_raw = random.choice(db["部位"])
            v_raw = random.choice(db["氛围"])
            
            # 去掉分组括号显示在卡片上
            s = s_raw.split('/')[-1]; sty = sty_raw.split('/')[-1]
            p = p_raw.split('/')[-1]; v = v_raw.split('/')[-1]
            
            with res_cols[i % 2]:
                st.markdown(f"""
                <div class="res-card">
                    <div style="color:#0071e3; font-size:12px; font-weight:700;">PROPOSAL {i+1}</div>
                    <div style="font-size:18px; margin:8px 0; font-weight:600;">{sty}风格 - {s}</div>
                    <div style="font-size:14px; opacity:0.8; margin-bottom:10px;">部位：{p} | 氛围：{v}</div>
                    <div style="background:rgba(0,113,227,0.05); padding:10px; border-radius:8px; font-size:12px; font-family:monospace;">
                        Prompt: {s}, {sty} tattoo style, {v}, on {p}, white background, high detail --v 6.0
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("资产库零件不足，请先在左侧录入素材！")
