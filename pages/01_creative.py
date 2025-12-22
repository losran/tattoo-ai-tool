import streamlit as st
import requests, base64, random, time
from openai import OpenAI

# --- 1. 核心配置 ---
# 移除了不再需要的 HF_TOKEN
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO = "losran/tattoo-ai-tool"

WAREHOUSE = {
    "Subject": "data/subjects.txt", "Action": "data/actions.txt", 
    "Style": "data/styles.txt", "Mood": "data/moods.txt", "Usage": "data/usage.txt"
}
GALLERY_FILE = "gallery/inspirations.txt"

# --- 2. 工具函数 ---
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

# --- 3. 初始化与布局 ---
st.title("🎨 创意引擎")

# 确保所有变量名都存在，防止 Attribute Error
for key in ['selected_prompts', 'generated_cache', 'polished_text', 'img_tags']:
    if key not in st.session_state:
        st.session_state[key] = [] if 'text' not in key else ""

col_main, col_gallery = st.columns([5, 2])

with col_gallery:
    st.subheader("📦 资产预览")
    mode = st.radio("预览模式", ["素材仓库", "灵感成品"], horizontal=True)
    with st.container(height=600):
        if mode == "素材仓库":
            cat = st.selectbox("分类", list(WAREHOUSE.keys()))
            words = get_github_data(WAREHOUSE[cat])
            if words:
                for w in words: st.button(w, key=f"w_{w}", use_container_width=True)
            else:
                st.caption("暂无数据或连接失败")
        else:
            insps = get_github_data(GALLERY_FILE)
            if insps:
                for i in insps: st.write(f"· {i}")
            else:
                st.caption("灵感库为空")

with col_main:
    # ==================================================
    # 📍 这里是改动最大的地方！旧的图片上传被替换成了这个：
    # ==================================================
    with st.expander("📸 灵感快速拆解 (手动描述)", expanded=True):
        st.caption("因免费图片接口不稳定，现改为手动输入描述，由 DeepSeek 精准拆解。")
        # 使用 text_area 让输入更方便
        user_img_desc = st.text_area("输入画面描述（例如：一条黑灰写实风格的龙，盘绕着牡丹花，眼神凶狠）：", height=80)

        if st.button("🔍 智能拆解为标签", type="primary", use_container_width=True):
            if user_img_desc and len(user_img_desc.strip()) > 2:
                with st.spinner("DeepSeek 正在深度分析画面结构..."):
                    # 调用 DeepSeek 进行语义拆解
                    try:
                        system_prompt = "你是一个顶级纹身艺术总监。你的任务是将用户的画面描述精准拆解为标准的纹身设计要素。格式必须是：Subject:主体词|Action:动作词|Style:风格词|Mood:氛围词|Usage:部位或用途词。全部使用中文，不要有多余废话。"
                        res = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"请拆解这段描述：{user_img_desc}"}
                            ],
                            temperature=0.2 # 降低随机性，让拆解更准确
                        ).choices[0].message.content
                        
                        # 存入状态
                        st.session_state.img_tags = res
                        st.success(f"✅ 解析成功：{res}")
                    except Exception as e:
                        st.error(f"DeepSeek 连接失败: {str(e)}")
            else:
                st.warning("⚠️ 请先输入具体的画面描述后再点解析。")
    # ==================================================
    # 📍 改动结束
    # ==================================================

    st.divider()

    # --- 生成逻辑 ---
    num = st.slider("生成几条创意？", 1, 10, 3)
    if st.button("🔥 一键生成方案", type="primary", use_container_width=True):
        st.session_state.generated_cache = []
        db_all = {k: get_github_data(v) for k, v in WAREHOUSE.items()}
        # 简单的容错处理，防止某个文件为空
        valid_cats = [cat for cat in db_all if db_all[cat]]
        if not valid_cats:
             st.error("素材库数据读取失败，请检查网络或 GitHub 文件。")
        else:
            for i in range(num):
                sample = []
                for cat in ["Subject", "Action", "Style", "Mood", "Usage"]:
                    # 如果该分类有数据就随机取一个，否则留空
                    if db_all.get(cat):
                        sample.append(random.choice(db_all[cat]))
                
                base_p = " + ".join(sample)
                # 融合图片标签
                final_p = f"参考图特征({st.session_state.img_tags}) + {base_p}" if st.session_state.img_tags else base_p
                st.session_state.generated_cache.append(final_p)
            st.rerun()

    # --- 方案库展示 ---
    if st.session_state.generated_cache:
        cols = st.columns(2)
        for idx, prompt in enumerate(st.session_state.generated_cache):
            with cols[idx % 2]:
                is_sel = prompt in st.session_state.selected_prompts
                with st.container(border=True):
                    st.markdown(f"**方案 {idx+1}** {' ✅' if is_sel else ''}")
                    st.caption(prompt)
                    if st.button("选择" if not is_sel else "取消", key=f"sel_{idx}", use_container_width=True):
                        if is_sel: st.session_state.selected_prompts.remove(prompt)
                        else: st.session_state.selected_prompts.append(prompt)
                        st.rerun()

    # --- 润色与跳转区 ---
    if st.session_state.selected_prompts:
        st.divider()
        if st.button("✨ DeepSeek 艺术润色", type="primary", use_container_width=True):
            with st.spinner("正在构思..."):
                combined = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(st.session_state.selected_prompts)])
                # 优化了提示词，让 DeepSeek 输出的格式更便于后续拆分
                system_prompt = "你是一个纹身艺术顾问。将标签转化为优美的中文提示词。请严格按照'**方案X：** 内容'的格式输出，每个方案之间用换行分隔。"
                res = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": combined}]
                ).choices[0].message.content
                st.session_state.polished_text = res

    # 只要有润色结果，就显示【保存】和【跳转】按钮
    if st.session_state.get('polished_text'):
        st.success("✅ 润色完成！")
        final_content = st.text_area("最终成果预览：", st.session_state.polished_text, height=250)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 存入云端灵感库", use_container_width=True):
                current = get_github_data(GALLERY_FILE)
                # 更精准的按行拆分，防止空行
                new_lines = [l.strip() for l in final_content.split('\n') if l.strip() and not l.startswith('**')]
                if new_lines:
                    current.extend(new_lines)
                    if save_to_github(GALLERY_FILE, current):
                        st.balloons()
                        st.success(f"已成功存入 {len(new_lines)} 条灵感！")
                    else:
                        st.error("保存失败，请检查 GitHub 连接。")
                else:
                     st.warning("没有检测到有效内容可保存。")

        
        with c2:
            # 跳转按钮
            if st.button("🚀 发送到自动化跑图", type="primary", use_container_width=True):
                st.session_state.auto_input_cache = final_content
                st.switch_page("pages/02_automation.py")
