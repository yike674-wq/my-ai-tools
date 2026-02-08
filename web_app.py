import streamlit as st
import pandas as pd

from PyPDF2 import PdfReader

from openai import OpenAI

# --- 1. 页面基础配置 ---

st.set_page_config(page_title="AI 智能助手 (增强版)", layout="wide")

# --- 2. 初始化记忆 (让 AI 不会秒忘) ---

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# --- 3. 侧边栏配置 ---

with st.sidebar:
    st.header("🔑 安全配置")
    api_key = st.text_input("请输入您的 DeepSeek API Key", type="password")
    
    st.header("📂 文件上传")
    uploaded_file = st.file_uploader("支持 PDF, Excel, CSV", type=["pdf", "xlsx", "csv"])
    
    st.markdown("---")
    st.info("💡 提示：如果 PDF 是扫描件（纯图片），AI 无法读取。请使用可复制文字的 PDF。")

# --- 4. 主界面标题 ---

st.title("🤖 AI 全能分析助手 (Pro 版)")

# --- 5. 文件处理核心逻辑 (带诊断功能) ---

file_content = ""

if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1].lower()
    
    try:
        # 处理 PDF
        if file_type == "pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    file_content += text + "\n"
            
            # === 关键诊断代码 ===
            if len(file_content.strip()) == 0:
                st.error("⚠️ 警告：检测到文件内容为空！\n这很可能是一个【扫描版/纯图片 PDF】。AI 无法读取图片中的文字，请上传可选中文本的 PDF。")
            else:
                st.success(f"✅ PDF 读取成功！共检测到 {len(file_content)} 个字符。AI 已准备好回答。")

        # 处理 Excel
        elif file_type in ["xlsx", "xls"]:
            df = pd.read_excel(uploaded_file)
            # 转换为文本供 AI 阅读
            file_content = df.to_string() 
            st.success(f"✅ Excel 表格已加载！包含 {len(df)} 行数据。")

        # 处理 CSV
        elif file_type == "csv":
            df = pd.read_csv(uploaded_file)
            file_content = df.to_string()
            st.success(f"✅ CSV 数据已加载！包含 {len(df)} 行数据。")
            
    except Exception as e:
        st.error(f"❌ 文件读取发生错误: {str(e)}")

# --- 6. 显示聊天历史 ---

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- 7. 处理用户输入 ---

# 如果没有 API Key，禁止输入
if not api_key:
    st.warning("👈 请先在左侧侧边栏输入您的 API Key")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

user_input = st.chat_input("请输入您的问题...")

if user_input:
    # 显示用户的提问
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # 构造发给 AI 的最终提示词
    # 如果有文件内容，就拼接到提示词里；如果没有，就只发问题
    if file_content:
        # 截取前 30000 个字符防止太长报错，通常够用了
        final_prompt = f"以下是用户上传的文件内容：\n\n{file_content[:30000]}\n\n用户问题：{user_input}"
    else:
        final_prompt = user_input

    # 调用 DeepSeek
    try:
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的数据分析助手。请根据用户上传的文件内容回答问题。"},
                    # 注意：这里我们简化处理，只发当前最新的问题和文件，避免 token 消耗过大
                    {"role": "user", "content": final_prompt} 
                ],
                stream=True
            )
            response = st.write_stream(stream)
            
        # 记住 AI 的回复
        st.session_state["messages"].append({"role": "assistant", "content": response})

    except Exception as e:
        st.error(f"AI 通讯出错: {e} \n请检查 API Key 是否正确。")