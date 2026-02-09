import streamlit as st
import pandas as pd

from PyPDF2 import PdfReader

from openai import OpenAI

import io
st.set_page_config(page_title="AI 资深数据分析师", layout="wide")

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
    st.info("💡 提示：AI 现在已升级为“审计模式”，会自动检测数据异常。")

# --- 4. 主界面标题 ---
st.title("🕵️‍♂️ AI 资深数据分析师 (审计版)")

# --- 5. 文件处理逻辑 ---
file_content = ""

if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1].lower()
    
    try:
        # 处理 PDF
        if file_type == "pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                text = page.extract_text()
                if text: file_content += text + "\n"
            
            if len(file_content.strip()) == 0:
                st.error("⚠️ 警告：检测到文件内容为空（可能是扫描件）。")
            else:
                st.success(f"✅ PDF 读取成功！共 {len(file_content)} 字符。")

        # 处理 Excel/CSV
        elif file_type in ["xlsx", "xls", "csv"]:
            if file_type == "csv":
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # 将数据转为文本，方便 AI 阅读
            file_content = df.to_string()
            st.success(f"✅ 表格已加载！包含 {len(df)} 行数据。")

            # === 下载按钮 (保持不变) ===
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
            
            st.download_button(
                label="📥 下载当前 Excel 文件",
                data=buffer.getvalue(),
                file_name=f"processed_{uploaded_file.name}",
                mime="application/vnd.ms-excel"
            )

    except Exception as e:
        st.error(f"❌ 出错了: {str(e)}")

# --- 6. 聊天界面 ---
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if not api_key:
    st.warning("👈 请先输入 API Key")
    st.stop()

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
user_input = st.chat_input("请输入问题...")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # === 🧠 关键修改：植入“资深分析师”的人设 ===
    # 我们定义一个超级详细的 System Prompt
    system_prompt = """
    你是一位拥有 10 年经验的资深数据分析师。
    你的任务是帮助用户清理数据、发现异常并提供决策建议。
    请分析用户提供的数据，并执行以下操作：
    1. 寻找异常：自动识别数据中的逻辑错误、缺失值或极端数值。
    2. 发现趋势：告诉用户数据里有没有明显的增长或下降规律。
    3. 去重统计：主动报告重复的数据行。
    4. 可视化建议：建议用户应该用什么图表来展示这些数据最合适。
    """
    # 构造最终提示词
    if file_content:
        final_prompt = f"以下是用户上传的文件数据：\n\n{file_content[:30000]}\n\n用户的具体问题是：{user_input}"
    else:
        final_prompt = user_input

    try:
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt}, # 这里用了新的设定
                    {"role": "user", "content": final_prompt}
                ],
                stream=True
            )
            response = st.write_stream(stream)
        st.session_state["messages"].append({"role": "assistant", "content": response})
    except Exception as e:
        st.error(f"AI 通讯失败: {e}")