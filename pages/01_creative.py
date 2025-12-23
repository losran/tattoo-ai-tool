import streamlit as st
import json
import os
import random
import numpy as np
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
def smart_sample_with_ai(category, user_intent, inventory):
    if not user_intent or not user_intent.strip():
        return random.choice(inventory) if inventory else "空"
    prompt = f"意图：{user_intent}\n分类：{category}\n词库：{inventory}\n任务：选一个词。只返回词汇。"
    try:
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}], temperature=0.3)
        return res.choices[0].message.content.strip()
    except: return random.choice(inventory)

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
    """
    智能预选词库：仅在有输入意图时调用
    """
    if not user_intent or len(inventory) <= limit:
        return random.sample(inventory, min(len(inventory), limit))
    
    prompt = f"意图：{user_intent}\n分类：{category}\n词库：{inventory}\n任务：从中挑选出最符合意图的 {limit} 个词。只返回词汇，逗号分隔。"
    try:
        res = client.chat.completions.create(
            model="deepseek-chat", 
            messages=[{"role": "user", "content": prompt}], 
            temperature=0.3
        )
        filtered_words = res.choices[0].message.content.replace("，", ",").split(",")
        # 确保选出来的词确实在词库里
        valid_words = [w.strip() for w in filtered_words if w.strip() in inventory]
        return valid_words if valid_words else random.sample(inventory, limit)
    except:
        return random.sample(inventory, limit)
        
# --- 3. UI 布局与 Session 初始化 ---
st.set_page_config(layout="wide", page_title="Creative Engine")

# 💡 初始化核心变量
for key in ['selected_prompts', 'generated_cache', 'history_log', 'polished_text', 'manual_editor']:
    if key not in st.session_state:
        st.session_state[key] = "" if 'editor' in key or 'text' in key else []
        
# 🔒 定义全局锁定状态
is_working = len(st.session_state.polished_text) > 0

st.title("🎨 创意引擎")
col_main, col_gallery = st.columns([5, 2.5])

# --- 🟢 右侧：仓库管理 (上) + 历史记录 (下) ---
with col_gallery:
    st.subheader("📦 仓库管理")
    mode = st.radio("模式", ["素材仓库", "灵感成品"], horizontal=True)
    
    # 1. 仓库管理容器
    with st.container(height=300, border=True):
        if mode == "素材仓库":
            cat = st.selectbox("分类", list(WAREHOUSE.keys()))
            words = get_github_data(WAREHOUSE[cat])
            if words:
                for w in words:
                    if st.checkbox(f" {w}", key=f"cat_{cat}_{w}", disabled=is_working):
                        if not is_working and w not in st.session_state.selected_prompts:
                            st.session_state.selected_prompts.append(w)
        else:
            insps = get_github_data(GALLERY_FILE)
            if insps:
                for i in insps:
                    if st.checkbox(i, key=f"insp_lib_{abs(hash(i))}", disabled=is_working):
                        if not is_working and i not in st.session_state.selected_prompts:
                            st.session_state.selected_prompts.append(i)

    # 📜 历史档案区 (永驻下方)
    st.divider()
    st.subheader("📜 历史档案")
    if st.session_state.history_log:
        with st.container(height=400, border=True):
            for h_idx, h_text in enumerate(st.session_state.history_log):
                is_checked = h_text in st.session_state.selected_prompts
                if st.checkbox(f"备选 {h_idx+1}: {h_text}", key=f"h_l_{h_idx}", value=is_checked, disabled=is_working):
                    if not is_working:
                        if h_text not in st.session_state.selected_prompts:
                            st.session_state.selected_prompts.append(h_text)
                            st.rerun()
        
        if st.button("🗑️ 清空历史", use_container_width=True, disabled=is_working):
            st.session_state.history_log = []
            st.rerun()

# --- 🔵 左侧：核心生成区 ---
with col_main:
    # 1. 顶部控制栏：流派调性（点选） + 创意混乱度（滑块）
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        # 使用 st.pills 或 st.radio 营造点选感
        style_tone = st.radio(
            "🎭 风格调性点选",
            options=["自由盲盒", "可爱柔美", "轻盈水彩", "日式传统", "欧美极简"],
            horizontal=True,
            index=3, # 默认选中日式传统
            help="点击切换不同的视觉灵魂"
        )
    with col_cfg2:
        # 混乱度保留滑块，因为它属于“程度”调节，更适合拖拽
        chaos_level = st.slider("🌀 创意碰撞 (混乱度)", 0, 100, 50)

    # 2. 意图输入
    intent_input = st.text_area("✍️ 组合意图输入框", placeholder="输入关键词，如：宇航员、玫瑰...", height=100)
    st.session_state.manual_editor = intent_input

    # 3. 按钮行：左侧激发按钮 + 右侧数量数字
    # 这里微调比例 [4.2, 1] 让按钮和数字框更贴合
    col_btn_btn, col_btn_num = st.columns([4.2, 1]) 
    with col_btn_btn:
        execute_button = st.button("🔥 激发创意组合", type="primary", use_container_width=True, disabled=is_working)
    with col_btn_num:
        num = st.number_input("数量", 1, 10, 6, label_visibility="collapsed")

    # --- 按钮执行逻辑 ---
    if execute_button:
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        
        with st.spinner("AI 正在释放灵感碰撞..."):
            has_intent = bool(intent_input.strip())
            
            # A. 风格倾向性引导
            style_mapping = {
                "可爱柔美": "可爱治愈风格",
                "轻盈水彩": "写意透明水彩风格",
                "日式传统": "日式 Old School 风格",
                "欧美极简": "欧美冷峻极简风格",
                "自由盲盒": "完全随机、不设限的艺术风格"
            }
            tone_name = style_mapping.get(style_tone, "自由发挥")

            # B. 词库预选（如果有输入就辅助选词，没有就随机）
            smart_sample_db = {}
            for k, v in db_all.items():
                if has_intent:
                    try:
                        smart_sample_db[k] = ai_pre_filter(k, intent_input, v, limit=20)
                    except:
                        smart_sample_db[k] = random.sample(v, min(len(v), 20))
                else:
                    smart_sample_db[k] = random.sample(v, min(len(v), 25))

            # C. 核心指令：找回最初那种“自由堆叠”的感觉
            # 删掉了一切死板的格式限制，只要“风格+主体+随机词”
            fast_prompt = f"""
            你是一位顶级的纹身艺术设计师。请根据以下要求给出 {num} 个极具视觉冲击力的纹身方案。
            
            【核心要求】：
            1. 每个方案必须以“{tone_name}”为基调。
            2. 每个方案的核心必须包含“{intent_input if has_intent else '随机灵感'}”。
            3. 重点：请围绕核心，从词库中自由组合 5 到 8 个词汇。不要死板，要有一种“破碎、拼贴、意识流”的艺术感。
            4. 方案格式：风格词 + 主体词 + 随机动作 + 随机氛围词 + 随机身体部位（不需要固定顺序，词多一点没关系）。

            【参考词库】：
            {smart_sample_db}

            【注意事项】：
            - 每一行代表一个方案。
            - 每个方案内的词请用“，”隔开。
            - 严禁输出大括号、键值对或 JSON。
            - 只输出方案列表，禁止解释说明。
            """

            try:
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": fast_prompt}],
                    temperature= 0.5 + (chaos_level / 100) * 0.45 # 脑洞越大，越自由
                )
                raw_content = res.choices[0].message.content.strip()
                
                # 清洗数据，只留文字
                raw_list = raw_content.split('\n')
                st.session_state.generated_cache = [
                    line.replace('"', '').replace('{', '').replace('}', '').replace('方案', '').replace(': ', '').strip() 
                    for line in raw_list if "，" in line or "," in line
                ][:num]
                st.rerun()
            except Exception as e:
                st.error(f"激发失败: {e}")
# --- 4. 润色区与【关键自动化入口】 ---
if st.session_state.selected_prompts and not st.session_state.polished_text:
    st.divider()
    if st.button("✨ 确认并转化为绘画提示词 (含方案锚点)", type="primary", use_container_width=True):
        st.session_state.generated_cache = [] # 清理桌面
        
        with st.spinner(f"AI 正在执行【{style_tone}】风格的【{chaos_level}% 基因突变】并生成分段锚点..."):
            try:
                # 1. 风格基调 (Style DNA) - 保持你原版逻辑
                style_dict = {
                    "可爱柔美": "Vector Art, thick rounded outlines, pastel flat colors, sticker art, kawaii core, no shading",
                    "轻盈水彩": "Hand-drawn Watercolor, ink bleed effect, white negative space, artistic splash, soft edges, illustration",
                    "日式传统": "Ukiyo-e Style, bold black calligraphy lines, flat traditional colors, woodblock print texture, 2D",
                    "欧美极简": "Linework Tattoo, geometric abstraction, single weight line, black and white, minimalist vector",
                    "自由盲盒": "Pop Art, mixed media collage, glitch art, abstract shapes, bold graphic design"
                }
                current_style_tags = style_dict.get(style_tone, "2D Vector Art, clean lines")

                # 2. 混乱度逻辑 - 保持你原版逻辑
                if chaos_level <= 30:
                    chaos_instruction = "严格遵守风格定义，不要添加任何奇怪元素，保持画风纯正、传统、稳健。"
                elif chaos_level <= 70:
                    chaos_instruction = "在保持风格基础的同时，加入异质元素。例如：在传统风格中加入现代几何形状，或使用非传统的配色方案。"
                else:
                    chaos_instruction = """
                    执行【风格强行融合】：
                    1. 必须打破常规！例如：如果是日式风格，尝试用“欧美复古”或“中式可爱”材质去表现。
                    2. 制造反差感 (Contrast)！例如：可爱的外表下隐藏着水彩，或者极简线条中爆发出绚丽色彩。
                    3. 关键词要包含：Surrealism (超现实), Hybrid (混合体), Avant-garde (前卫), Glitch (故障感)。
                    """

                # 3. 构造 System Prompt - 微调要求让AI知道要逐行处理
                system_prompt = f"""
                你是一个专门设计【纹身贴纸 (Tattoo Sticker)】的 AI 指令专家。
                
                【绝对禁令】：
                ❌ 严禁出现：Photorealistic, 3D Render, Unreal Engine, Hyper-realistic, Photo.
                ❌ 严禁出现背景：必须是 Isolated on white background.
                
                【当前风格锚点】：
                {current_style_tags}
                
                【混乱度/融合指令 ({chaos_level}/100)】：
                {chaos_instruction}
                
                【任务】：
                将用户的**每一个**关键词方案，分别转化为中文 Prompt。
                Prompt 结构必须是：
                (Best Quality), (Tattoo Sticker:1.3), [风格词], [融合后的视觉描述],
                
                【输出格式】：
                请严格【逐行输出】，每一行对应一个方案。纯中文 Tag 列表，用逗号分隔，提示词应该丰富。
                """

                # 4. 发送请求 (这里的 raw_input 加了编号，帮AI对齐)
                input_lines = [f"Scheme {i+1}: {p}" for i, p in enumerate(st.session_state.selected_prompts)]
                raw_input = "\n".join(input_lines)
                
                res = client.chat.completions.create(
                    model="deepseek-chat", 
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"请逐行处理以下方案：\n{raw_input}"}
                    ], 
                    temperature=0.6 + (chaos_level / 200)
                )
                
                # 5. 物理分段 + 锚点植入 (核心修改)
                ai_output = res.choices[0].message.content.strip()
                ai_lines = [line for line in ai_output.split('\n') if line.strip()]
                
                final_output_list = []
                # 你的物理前缀
                prefix = "(Masterpiece), (Tattoo Sticker:1.4), (2D:1.3), white background, "
                
                # 循环拼接，确保每一行都有“方案X:”
                for idx, prompt_text in enumerate(ai_lines):
                    # 防止AI回传的行数多于或少于输入，做一个安全截断
                    if idx >= len(st.session_state.selected_prompts): break
                    
                    # 清洗一下AI可能自带的序号
                    clean_prompt = prompt_text.split(':')[-1].split('.')[-1].strip()
                    clean_prompt = clean_prompt.replace("Prompt:", "").replace("提示词:", "")
                    
                    # 组装：方案X: + 前缀 + 风格 + 内容
                    formatted_line = f"方案{idx+1}: {prefix} {current_style_tags}, {clean_prompt}"
                    final_output_list.append(formatted_line)
                
                # 如果AI偶尔抽风只回了一行，这里做一个兜底，强行把所有方案都列出来
                if not final_output_list and ai_output:
                     final_output_list.append(f"方案1: {prefix} {current_style_tags}, {ai_output}")

                st.session_state.polished_text = "\n\n".join(final_output_list)
                st.rerun()

            except Exception as e: 
                st.error(f"转化失败: {e}")

if st.session_state.polished_text:
    st.divider(); st.subheader("🎨 绘图提示词 (Ready)")
    
    st.text_area("提示词预览 (已加锚点)：", st.session_state.polished_text, height=300)
    
    # 自动化入口 (保证不丢！)
    c_auto_1, c_auto_2 = st.columns(2)
    with c_auto_1:
        if st.button("🚀 发送到自动化生成", type="primary", use_container_width=True):
            st.session_state.auto_input_cache = st.session_state.polished_text
            st.switch_page("pages/02_automation.py")
    with c_auto_2:
        if st.button("🔄 重新生成 (解锁)", use_container_width=True):
            st.session_state.polished_text = ""; st.rerun()
