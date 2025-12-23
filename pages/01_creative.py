import streamlit as st
import json
import os
import random
import requests
import base64
from openai import OpenAI
from style_manager import apply_pro_style

# 📍 视觉样式同步
apply_pro_style()

# --- 1. 核心配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

WAREHOUSE = {
    "Subject": "data/subjects.txt", 
    "Action": "data/actions.txt", 
    "Style": "data/styles.txt", 
    "Mood": "data/moods.txt", 
    "Usage": "data/usage.txt"
}
GALLERY_FILE = "gallery/inspirations.txt"

# --- 2. 核心函数 ---
def get_github_data(path):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return [line.strip() for line in base64.b64decode(resp.json()['content']).decode().splitlines() if line.strip()]
    except: pass
    return []

def save_to_github(path, data_list):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        get_resp = requests.get(url, headers=headers, timeout=10).json()
        content_str = "\n".join(list(set(data_list)))
        b64_content = base64.b64encode(content_str.encode()).decode()
        requests.put(url, headers=headers, json={"message": "update", "content": b64_content, "sha": get_resp.get('sha')}, timeout=15)
        return True
    except: return False

def ai_pre_filter(category, user_intent, inventory, limit=15):
    if not user_intent or len(inventory) <= limit:
        return random.sample(inventory, min(len(inventory), limit))
    prompt = f"意图：{user_intent}\n分类：{category}\n词库：{inventory}\n任务：从挑选符合意图的 {limit} 个词。只返回词汇，逗号分隔。"
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}], temperature=0.3)
        filtered = res.choices[0].message.content.replace("，", ",").split(",")
        valid = [w.strip() for w in filtered if w.strip() in inventory]
        return valid if valid else random.sample(inventory, limit)
    except: return random.sample(inventory, limit)

# --- 3. UI 布局与 Session 初始化 ---
st.set_page_config(layout="wide", page_title="Creative Engine")

for key in ['selected_prompts', 'generated_cache', 'history_log', 'polished_text', 'manual_editor']:
    if key not in st.session_state:
        st.session_state[key] = "" if 'editor' in key or 'text' in key else []

is_working = len(st.session_state.polished_text) > 0

st.title("🎨 创意引擎")
col_main, col_gallery = st.columns([5, 2.5])

# --- 🟢 右侧：管理区 ---
with col_gallery:
    st.subheader("📦 仓库管理")
    mode = st.radio("模式", ["素材仓库", "灵感成品"], horizontal=True)
    with st.container(height=300, border=True):
        if mode == "素材仓库":
            cat = st.selectbox("分类", list(WAREHOUSE.keys()))
            words = get_github_data(WAREHOUSE[cat])
            if words:
                for w in words:
                    if st.checkbox(f" {w}", key=f"cat_{cat}_{w}", disabled=is_working):
                        if w not in st.session_state.selected_prompts: st.session_state.selected_prompts.append(w)
        else:
            insps = get_github_data(GALLERY_FILE)
            if insps:
                for i in insps:
                    if st.checkbox(i, key=f"insp_{abs(hash(i))}", disabled=is_working):
                        if i not in st.session_state.selected_prompts: st.session_state.selected_prompts.append(i)
    st.divider()
    st.subheader("📜 历史档案")
    if st.session_state.history_log:
        with st.container(height=400, border=True):
            for h_idx, h_text in enumerate(st.session_state.history_log):
                if st.checkbox(f"备选 {h_idx+1}: {h_text}", key=f"h_{h_idx}", value=h_text in st.session_state.selected_prompts, disabled=is_working):
                    if h_text not in st.session_state.selected_prompts: st.session_state.selected_prompts.append(h_text); st.rerun()

# --- 🔵 左侧：生成核心区 ---
with col_main:
    c1, c2 = st.columns(2)
    with c1:
        style_tone = st.radio("🎭 风格调性点选", options=["自由盲盒", "可爱柔美", "轻盈水彩", "日式传统", "欧美极简"], horizontal=True, index=3)
    with c2:
        chaos_level = st.slider("🌀 创意碰撞 (混乱度)", 0, 100, 50)

    intent_input = st.text_area("✍️ 组合意图输入框", placeholder="输入关键词...", height=100)
    st.session_state.manual_editor = intent_input

    cb_btn, cb_num = st.columns([4, 1])
    with cb_btn:
        execute_button = st.button("🔥 激发创意组合", type="primary", use_container_width=True)
    with cb_num:
        num = st.number_input("数量", 1, 10, 6, label_visibility="collapsed")

    if execute_button:
        st.session_state.polished_text = "" # 点击即解锁
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        with st.spinner("🚀 灵感爆发中..."):
            has_intent = bool(intent_input.strip())
            style_map = {"可爱柔美": "可爱治愈", "轻盈水彩": "透明水彩", "日式传统": "日式Old School", "欧美极简": "极简几何", "自由盲盒": "前卫跨界"}
            tone = style_map.get(style_tone, "随机")
            smart_db = {k: ai_pre_filter(k, intent_input, v, 20) if has_intent else random.sample(v, min(len(v), 20)) for k, v in db_all.items()}
            
            prompt = f"风格：{tone}。意图：{intent_input if has_intent else '自由'}。从库中拼贴15-18个词形成艺术长句，每行一个，中文逗号分隔。禁止JSON。【核心要求】： 1. 不要死板！请从词库中自由组合 10-18 个词汇。 2. 结构：风格 + 主体 + 随机动作 + 随机氛围 + 身体部位。 3. 要有一种“破碎、拼贴”的艺术感，词汇之间要有反差。 4. 输出格式：纯中文，用逗号分隔。参考库：{smart_db}"
            
            try:
                res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}], temperature=0.5+(chaos_level/200))
                lines = res.choices[0].message.content.strip().split('\n')
                st.session_state.generated_cache = [l.split(':')[-1].strip() for l in lines if "，" in l or "," in l][:num]
                st.rerun()
            except Exception as e: st.error(f"失败: {e}")

    if st.session_state.generated_cache:
        st.divider(); st.subheader("🎲 方案筛选")
        cols = st.columns(2)
        for idx, p in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = p in st.session_state.selected_prompts
                if st.button(f"{idx+1}. {p}", key=f"g_{idx}", type="primary" if is_sel else "secondary", use_container_width=True):
                    if is_sel: st.session_state.selected_prompts.remove(p)
                    else: st.session_state.selected_prompts.append(p)
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        ct1, ct2 = st.columns(2)
        with ct1:
            if st.button("💾 确认存入成品库", use_container_width=True, type="secondary"):
                if st.session_state.selected_prompts:
                    cur = get_github_data(GALLERY_FILE)
                    cur.extend(st.session_state.selected_prompts)
                    if save_to_github(GALLERY_FILE, cur): st.toast("✅ 已存档")
        with ct2:
            if st.button("🗑️ 清空看板并强行解锁", use_container_width=True, type="secondary"):
                st.session_state.generated_cache = []; st.session_state.selected_prompts = []; st.session_state.polished_text = ""; st.rerun()

# --- 4. 润色区：纯中文词组语境优化 ---
if st.session_state.selected_prompts and not st.session_state.polished_text:
    st.divider()
    if st.button("✨ 确认方案并开始艺术润色", type="primary", use_container_width=True):
        st.session_state.generated_cache = [] 
        with st.spinner("正在优化中文语境..."):
            try:
                # 将选中的方案拼成列表发给 AI
                combined = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(st.session_state.selected_prompts)])
                
                # 核心指令：纯中文处理，仅修饰语境
                system_instruction = f"""
                你正在为【纹身贴（Tattoo Sticker）】整理可直接用于生产与展示的图形描述。
                
                【核心任务】：
                将用户给出的中文关键词，重组为一条【明确体现“贴纸属性、图形完整度与视觉识别性”】的中文描述。
                
                【强制长度要求】：
                - 每一条方案不少于 50 个汉字
                - 字数不足视为不合格，必须重写
                参考案例：Y2K 气质的羽毛作为主体造型，以纵向拉伸的轮廓构成主形，线条偏细但在羽轴处加粗，形成明显的针触节奏变化，暗色块面集中于边缘以强化锐利感，留白用于区分羽片层次，整体偏 new school 与线稿混合风格，构图顺着锁骨与脊柱走向延展，贴合骨骼纵向生长，呈现冷感而紧绷的刺青气质。
                
                【内容必须覆盖的维度（每条都要有）】：
                1. 图形主体是什么，以及最容易被识别的视觉特征
                2. 整体轮廓是否清晰，是否适合模切成独立贴纸
                3. 线条与块面的组织方式（偏线稿 / 偏块面 / 混合）
                4. 是否为纯平、矢量感、无阴影的贴纸视觉
                5. 推荐的贴附区域（如手腕内侧、耳后、脚踝等）
                6. 整体视觉气质（轻松、可爱、冷感、酷感等，避免文学修辞）
                
                【允许】：
                - 为了让画面更像“贴纸”，可以补充轮廓、边界、白底、贴纸感等描述
                - 可以重复强调“平面、干净、图形化”
                
                【禁止】：
                - 禁止真实刺青、针触、入皮、渗墨等纹身语言
                - 禁止摄影、灯光、写实皮肤描写
                - 禁止故事化、情绪抒情
                
                【强制规则】：
                1. 必须输出纯中文，严禁出现任何英文或拼音。
                2. 允许新增用户未提供的视觉元素、情绪概念或隐喻。
                3. 允许替换连接词，但不得扩写成文学段落。
                4. 禁止使用“仿佛、宛如、像是、象征、隐喻”等文学修辞。
                5. 内容应保持“设计说明级别”，而非散文或文案。
                6. 段落内必须包含“纹身贴”字样。
                
                【结构要求】：
                - 必须以 '**方案X：**' 开头，保留双星号以便程序识别。
                - 后面只跟一整句整理后的描述
                - 不要加解释、不要加评价、不要加结尾总结
                
                【风格约束】：
                - 风格倾向：{style_tone}
                - 混乱度：{chaos_level}/100
                  - 低混乱：语义清晰、结构稳定
                  - 高混乱：允许语序打散，但不得引入新概念
                
                请严格按照以上规则逐行输出。
                """

                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": f"请把这些方案润色得更通顺高级：\n{combined}"}
                    ],
                    temperature=0.7 # 适中的随机性让文采更好
                ).choices[0].message.content

                st.session_state.polished_text = res
                st.rerun()
            except Exception as e:
                st.error(f"润色失败: {e}")

# --- 最终展示区 (锚点分段的关键) ---
if st.session_state.get('polished_text'):
    st.divider()
    st.subheader("🎨 艺术润色成品")
    # 这里的 final_content 出来的就是带有 **方案X：** 的中文内容
    final_content = st.text_area("内容预览：", st.session_state.polished_text, height=350)
    
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    with c_btn1:
        if st.button("💾 存入成品库", use_container_width=True):
            current = get_github_data(GALLERY_FILE)
            # 过滤掉方案字样，只存内容
            new = [l.strip() for l in final_content.split('\n') if l.strip()]
            current.extend(new); save_to_github(GALLERY_FILE, current); st.success("已存档")
    with c_btn2:
        if st.button("🚀 发送到自动化", type="primary", use_container_width=True):
            # 将带“方案”锚点的中文文本传给下一页
            st.session_state.auto_input_cache = final_content
            st.switch_page("pages/02_automation.py")
    with c_btn3:
        if st.button("🔄 重新调配", use_container_width=True):
            st.session_state.polished_text = ""; st.rerun()
