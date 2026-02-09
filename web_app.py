import streamlit as st
import pandas as pd

from PyPDF2 import PdfReader

from openai import OpenAI

import io  # 新增：用于处理文件下载的工具
st.set_page_config(page_title="AI 智能助手 (Pro+下载版)", layout="wide")

# --- 2. 初始化记忆 ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# --- 3. 侧边栏配置 ---
with st.sidebar:
    st.header("🔑 安全配置")
    api_key = st.text_input("请输入您的 DeepSeek API Key", type="password")
    
    st.header("📂 文件上传")
    uploaded_file = st.file_uploader("支持 PDF, Excel, CSV", type=["pdf", "xlsx", "csv"])
    
    st.markdown("---")
    st.info("💡 下载功能已上线！上传 Excel 后即可看到下载按钮。")

# --- 4. 主界面标题 ---
st.title("🤖 AI 全能分析助手 (Pro+版)")

# --- 5. 文件处理逻辑 ---
file_content = ""

if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1].lower()
    
    try:
        if file_type == "pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                text = page.extract_text()
                if text: file_content += text + "\n"
            
            if len(file_content.strip()) == 0:
                st.error("⚠️ 警告：检测到文件内容为空（可能是扫描件）。")
            else:
                st.success(f"✅ PDF 读取成功！共 {len(file_content)} 字符。")

        elif file_type in ["xlsx", "xls", "csv"]:
            if file_type == "csv":
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            file_content = df.to_string()
            st.success(f"✅ 表格已加载！包含 {len(df)} 行数据。")

            # === ✨ 新增功能：下载按钮 ===
            # 将 DataFrame 转换回 Excel 格式供下载
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            
            st.download_button(
                label="📥 点击下载处理后的 Excel 文件",
                data=buffer.getvalue(),
                file_name=f"processed_{uploaded_file.name}",
                mime="application/vnd.ms-excel"
            )

    except Exception as e:
        st.error(f"❌ 出错了: {str(e)}")

# --- 6. 聊天界面 (保持不变) ---
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if not api_key:
    st.warning("👈 请先输入 API Key")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
user_input = st.chat_input("针对此文件提问...")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    if file_content:
        final_prompt = f"文件内容：\n{file_content[:30000]}\n问题：{user_input}"
    else:
        final_prompt = user_input

    try:
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的数据分析助手。"},
                    {"role": "user", "content": final_prompt}
                ],
                stream=True
            )
            response = st.write_stream(stream)
        st.session_state["messages"].append({"role": "assistant", "content": response})
    except Exception as e:
        st.error(f"AI 通讯失败: {e}")