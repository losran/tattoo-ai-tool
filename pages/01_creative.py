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
    "Mood": "data/moods.txt",
    "Usage": "data/usage.txt",

    # 👇 新增的风格分层
    "StyleSystem": "data/styles_system.txt",
    "Technique": "data/styles_technique.txt",
    "Color": "data/styles_color.txt",
    "Texture": "data/styles_texture.txt",
    "Composition": "data/styles_composition.txt",
    "Accent": "data/styles_accent.txt"
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

if execute_button:
    st.session_state.polished_text = ""  # 解锁
    db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}

    with st.spinner("🚀 灵感爆发中..."):
        new_batch = []

        # ===== ① 从分层仓库取词（第三步）=====
        subjects = smart_sample_with_ai("Subject", intent_input, db_all["Subject"], chaos_level)
        actions  = smart_sample_with_ai("Action",  intent_input, db_all["Action"],  chaos_level)
        moods    = smart_sample_with_ai("Mood",    intent_input, db_all["Mood"],    chaos_level)
        usages   = smart_sample_with_ai("Usage",   intent_input, db_all["Usage"],   chaos_level)

        style_system  = smart_sample_with_ai("StyleSystem",  intent_input, db_all["StyleSystem"],  chaos_level)
        style_tech    = smart_sample_with_ai("Technique",    intent_input, db_all["Technique"],    chaos_level)
        style_color   = smart_sample_with_ai("Color",        intent_input, db_all["Color"],        chaos_level)
        style_texture = smart_sample_with_ai("Texture",      intent_input, db_all["Texture"],      chaos_level)
        style_comp    = smart_sample_with_ai("Composition",  intent_input, db_all["Composition"],  chaos_level)
        style_accent  = smart_sample_with_ai("Accent",       intent_input, db_all["Accent"],       chaos_level)

        # ===== ② chaos → 取词数量映射 =====
        def chaos_pick(c, low, mid, high):
            if c < 30:
                return random.randint(*low)
            elif c < 70:
                return random.randint(*mid)
            else:
                return random.randint(*high)

        for _ in range(num):
            s  = random.sample(subjects, min(len(subjects), 1))
            a  = random.sample(actions,  min(len(actions), chaos_pick(chaos_level, (1,1),(1,2),(2,3))))
            m  = random.sample(moods,    min(len(moods),   chaos_pick(chaos_level, (1,2),(2,3),(3,4))))

            ss = random.sample(style_system,  min(len(style_system), 1))
            st = random.sample(style_tech,    min(len(style_tech),   chaos_pick(chaos_level,(1,2),(2,3),(3,4))))
            sc = random.sample(style_color,   min(len(style_color),  1))
            sx = random.sample(style_texture, min(len(style_texture),chaos_pick(chaos_level,(0,1),(1,1),(1,2))))
            sp = random.sample(style_comp,    min(len(style_comp),   1))

            sa = []
            if chaos_level > 60 and style_accent:
                sa = random.sample(style_accent, 1)

            u  = random.sample(usages, min(len(usages), 1))

            # ===== ③ 最终拼接（结构稳定）=====
            new_batch.append(
                f"{'，'.join(s)}，"
                f"{'，'.join(ss)}，{'，'.join(st)}，{'，'.join(sc)}，"
                f"{'，'.join(sx)}，{'，'.join(sp)}，"
                f"{'，'.join(a)}，{'，'.join(m)}，"
                + (f"{'，'.join(sa)}，" if sa else "")
                + f"纹在{'，'.join(u)}"
            )

        st.session_state.generated_cache = new_batch
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
                你正在为纹身师整理【可直接用于落皮的刺青设计描述】。
                
                【核心任务】：
                将用户给出的中文关键词，重组为一条【信息密度充足、结构完整、具备明确刺青语言】的中文描述。
                
                【强制长度要求】：
                - 每一条方案不少于 50 个汉字
                - 字数不足视为不合格，必须重写
                参考案例：Y2K 气质的羽毛作为主体造型，以纵向拉伸的轮廓构成主形，线条偏细但在羽轴处加粗，形成明显的针触节奏变化，暗色块面集中于边缘以强化锐利感，留白用于区分羽片层次，整体偏 new school 与线稿混合风格，构图顺着锁骨与脊柱走向延展，贴合骨骼纵向生长，呈现冷感而紧绷的刺青气质。
                
                【内容结构要求（每条都必须覆盖）】：
                1. 主体造型与整体轮廓（图形长什么样）
                2. 线条语言（粗细变化、连续或断裂、针触感）
                3. 块面与留白关系（密度、层次、负形使用）
                4. 明确的纹身风格指向（如 linework / new school / sketchy / 几何感等）
                5. 与身体部位的贴合方式（顺骨、内外侧、纵向或横向）
                6. 整体刺青气质（偏冷、偏锐、偏松弛等，但禁止文学修辞）
                
                【允许】：
                - 为了让画面更像“贴纸”，可以补充轮廓、边界、白底、贴纸感等描述
                - 可以重复强调“平面、干净、图形化”
                
                
                【强制规则】：
                1. 输出纯中文。
                2. 段落内必须包含“纹身”字样。
                
                【结构要求】：
                - 必须以 '**方案X：**' 开头，保留双星号以便程序识别。
                - 在每一行描述的最后，加上三个井号 '###' 作为结束符。
                
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
