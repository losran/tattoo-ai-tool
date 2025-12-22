import streamlit as st
import requests, base64, random, time
from openai import OpenAI

# --- 1. 基础配置 ---
client = OpenAI(api_key=st.secrets["DEEPSEEK_KEY"], base_url="https://api.deepseek.com")
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
HF_TOKEN = st.secrets.get("HF_TOKEN", "")
REPO = "losran/tattoo-ai-tool"
# 增加了 Inspiration 分类用于存储灵感
FILES = {
    "Subject": "subjects.txt", "Action": "actions.txt", 
    "Style": "styles.txt", "Mood": "moods.txt", "Usage": "usage.txt",
    "灵感库": "inspirations.txt"
}

# --- 2. 工具函数 ---
def get_data(filename):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return [line.strip() for line in base64.b64decode(resp.json()['content']).decode().splitlines() if line.strip()]
    return []

def sync_data(filename, data_list):
    url = f"https://api.github.com/repos/{REPO}/contents/data/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    get_resp = requests.get(url, headers=headers).json()
    content_str = "\n".join(list(set(data_list))) # 灵感库不强制排序，保持新鲜感
    b64_content = base64.b64encode(content_str.encode()).decode()
    requests.put(url, headers=headers, json={
        "message": "save inspiration", "content": b64_content, "sha": get_resp.get('sha')
    })

def get_image_desc(image_bytes):
    """
    更换了更稳定的模型，并增加了详细的调试信息
    """
    # 更换模型为 nlpconnect/vit-gpt2-image-captioning (非常稳定)
    API_URL = "https://api-inference.huggingface.co/models/nlpconnect/vit-gpt2-image-captioning"
    
    # 检查 Token 是否存在
    if not HF_TOKEN:
        st.error("❌ 错误：未检测到 HF_TOKEN。请检查 Streamlit Secrets 设置！")
        return None
        
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    try:
        for i in range(5):
            response = requests.post(API_URL, headers=headers, data=image_bytes)
            
            if response.status_code == 200:
                result = response.json()
                # 兼容不同模型的返回格式
                if isinstance(result, list): return result[0].get('generated_text')
                return result.get('generated_text')
            
            elif response.status_code == 503:
                st.warning(f"⏳ AI 模型正在初始化，请稍等... ({i+1}/5)")
                time.sleep(10)
                continue
            
            else:
                # 如果还是报错，直接把错误码显示出来方便排查
                st.error(f"抱脸接口报错: {response.status_code}")
                # 这里的调试信息能帮我们确认是不是 Token 没填对
                if "410" in str(response.status_code):
                    st.info("💡 提示：410 错误通常是接口地址变动。已尝试更换模型。")
                return None
    except Exception as e:
        st.error(f"网络异常: {str(e)}")
        return None
    return "解析超时"

def polish_prompts_chinese(prompt_list):
    combined_input = "\n".join([f"方案{i+1}: {p}" for i, p in enumerate(prompt_list)])
    system_prompt = "你是一个顶级的纹身艺术顾问。将标签转化为优美、有画面感的中文提示词。不要废话。"
    try:
        res = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"润色标签：\n{combined_input}"}],
            temperature=0.7
        )
        return res.choices[0].message.content
    except: return "润色失败"

# --- 3. 初始化状态 ---
for k in ['selected_prompts', 'generated_cache', 'polished_text', 'img_tags']:
    if k not in st.session_state: st.session_state[k] = [] if 'text' not in k else ""

# --- 4. 页面布局 ---
st.title("🎨 创意引擎 & 云端灵感库")
col_left, col_main, col_right = st.columns([1, 4, 2])

with col_right:
    st.subheader("📦 仓库预览")
    cat_view = st.selectbox("切换分类", list(FILES.keys()))
    words = get_data(FILES[cat_view])
    with st.container(height=600):
        if words:
            for w in words: st.text(w) # 灵感库文字长，用 text 显示更清晰
        else: st.caption("暂无数据")

with col_main:
    # 图片反推
    with st.expander("📸 参考图提取"):
        up_file = st.file_uploader("上传图", type=["jpg", "png", "jpeg"])
        if up_file:
            if st.button("🔍 开始反推"):
                with st.spinner("AI看图中..."):
                    desc = get_image_desc(up_file.getvalue())
                    if desc:
                        res = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "user", "content": f"拆解为五维标签(Subject|Action|Style|Mood|Usage)：{desc}"}]
                        ).choices[0].message.content
                        st.session_state.img_tags = res
                st.info(f"提取结果：{st.session_state.img_tags}")

    # 生成逻辑
    num_gen = st.slider("生成数量", 1, 10, 3)
    if st.button("🔥 一键生成", type="primary", use_container_width=True):
        st.session_state.generated_cache = []
        db_all = {k: get_data(v) for k, v in FILES.items() if k != "灵感库"}
        for i in range(num_gen):
            sample = [random.choice(db_all[cat]) if db_all.get(cat) else " " for cat in ["Subject", "Action", "Style", "Mood", "Usage"]]
            base_p = " + ".join(sample)
            final_p = f"参考图({st.session_state.img_tags}) + {base_p}" if st.session_state.img_tags else base_p
            st.session_state.generated_cache.append(final_p)
        st.rerun()

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

    # 汇总与保存
    if st.session_state.selected_prompts:
        st.divider()
        c1, c2 = st.columns(2)
        if c1.button("✨ DeepSeek 润色", type="primary", use_container_width=True):
            with st.spinner("构思中..."):
                st.session_state.polished_text = polish_prompts_chinese(st.session_state.selected_prompts)
        if c2.button("🗑️ 清空", use_container_width=True):
            st.session_state.selected_prompts = []; st.session_state.polished_text = ""; st.rerun()

        if st.session_state.polished_text:
            st.success("✅ 润色完成")
            txt_area = st.text_area("最终成果：", st.session_state.polished_text, height=200)
            
            if st.button("💾 存入云端灵感库", use_container_width=True):
                with st.spinner("正在同步至 GitHub..."):
                    current_insp = get_data(FILES["灵感库"])
                    # 按行拆分润色结果并存入
                    new_lines = [line.strip() for line in st.session_state.polished_text.split('\n') if line.strip()]
                    current_insp.extend(new_lines)
                    sync_data(FILES["灵感库"], current_insp)
                    st.balloons()
                    st.success("已永久存入灵感库！换台电脑也能看。")
