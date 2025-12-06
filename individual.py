import streamlit as st
import google.generativeai as genai
import json
import time

# ==========================================
# 1. 頁面基礎設定
# ==========================================
st.set_page_config(
    page_title="物品身世追蹤器 AI",
    page_icon="🔍",
    layout="centered"
)

# 自訂 CSS (時間軸樣式)
st.markdown("""
    <style>
    .step-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #3b82f6;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        transition: transform 0.2s;
        color: #1f2937;
    }
    .step-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
    }
    .step-header {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
    }
    .circle-number {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        background-color: #3b82f6;
        color: white;
        border-radius: 50%;
        margin-right: 12px;
        font-weight: bold;
        flex-shrink: 0;
    }
    .step-role {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827;
    }
    .step-industry {
        font-size: 0.75rem;
        background-color: #f3f4f6;
        color: #6b7280;
        padding: 2px 8px;
        border-radius: 9999px;
        margin-left: 10px;
        font-weight: 500;
    }
    .step-desc {
        color: #4b5563;
        line-height: 1.6;
        margin-left: 44px; /* Align with text start */
    }
    /* 隱藏 Streamlit 預設選單，讓介面更乾淨 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 啟動「上鎖的箱子」 (讀取 Secrets)
# ==========================================
try:
    # 嘗試從 Streamlit Cloud 的 Secrets 讀取 Key
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    # 如果找不到 (例如在本地執行)，給個提示
    api_key = None

# 如果沒有 Key，顯示警告並停止執行
if not api_key:
    st.error("⚠️ 系統未偵測到 API Key。")
    st.info("如果您是管理者，請前往 Streamlit Cloud 的 App Settings -> Secrets 設定 `GEMINI_API_KEY`。")
    st.stop()

# 設定 Gemini
genai.configure(api_key=api_key)

# ==========================================
# 3. AI 邏輯核心
# ==========================================
def get_gemini_response(query):
    # 使用支援搜尋的模型
    # 優先嘗試 gemini-2.0-flash-exp，如果失敗可改用 gemini-1.5-flash
    model = genai.GenerativeModel('gemini-2.0-flash-exp') 
    
    prompt = f"""
    使用者想要了解 "{query}" 這個物品是怎麼做出來的，以及經過哪些行業。
    請運用 Google Search 工具搜尋 "{query}" 的完整供應鏈與製造過程。
    
    請將結果整理成一個 JSON 物件，格式如下：
    {{
        "name": "{query}",
        "icon": "物品的 emoji (例如 🚗, ☕)",
        "steps": [
            {{
                "role": "擬人化的職業名稱 + Emoji (例如：林業人 🌲)",
                "industry": "所屬行業別",
                "desc": "簡短描述該步驟在做什麼 (約 20-30 字)"
            }}
        ]
    }}

    要求：
    1. 列出 5 到 8 個步驟，從原料到消費者。
    2. 使用繁體中文。
    3. 務必回傳純 JSON 字串，不要包含 ```json 等標記。
    """
    
    try:
        response = model.generate_content(
            contents=prompt,
            tools='google_search',
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"分析失敗，請稍後再試: {e}")
        return None

# ==========================================
# 4. 前端介面
# ==========================================
st.title("🔍 物品身世追蹤器")
st.markdown("輸入任何物品，AI 將即時搜尋全球供應鏈並為您解析它的前世今生。")

# 輸入區塊
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        user_input = st.text_input("輸入物品名稱", placeholder="例如：電動車、珍珠奶茶、晶片...", label_visibility="collapsed")
    with col2:
        analyze_btn = st.button("開始分析", use_container_width=True, type="primary")

# 快速範例
st.markdown("💡 **點擊試試看：**")
ex_col1, ex_col2, ex_col3, ex_col4 = st.columns(4)
if ex_col1.button("🚀 太空梭"): user_input = "太空梭"; analyze_btn = True
if ex_col2.button("🍜 拉麵"): user_input = "拉麵"; analyze_btn = True
if ex_col3.button("📱 iPhone"): user_input = "iPhone"; analyze_btn = True
if ex_col4.button("👟 球鞋"): user_input = "球鞋"; analyze_btn = True

# ==========================================
# 5. 執行與渲染
# ==========================================
if analyze_btn and user_input:
    with st.spinner(f"正在分析「{user_input}」的全球供應鏈資料..."):
        # 模擬一點延遲感
        time.sleep(0.5)
        data = get_gemini_response(user_input)

    if data:
        st.divider()
        st.header(f"{data.get('icon', '📦')} 分析結果：{data['name']}")
        
        # 渲染時間軸
        steps = data.get('steps', [])
        colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"] # 藍, 綠, 黃, 紅, 紫

        for index, step in enumerate(steps):
            border_color = colors[index % len(colors)]
            
            # 卡片 HTML
            st.markdown(f"""
            <div class="step-card" style="border-left-color: {border_color};">
                <div class="step-header">
                    <div class="circle-number" style="background-color: {border_color};">{index + 1}</div>
                    <div class="step-role">{step['role']}</div>
                    <div class="step-industry">{step['industry']}</div>
                </div>
                <div class="step-desc">{step['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 連接線 (除了最後一個步驟)
            if index < len(steps) - 1:
                st.markdown("""
                <div style="margin-left: 15px; height: 20px; border-left: 2px dashed #d1d5db;"></div>
                """, unsafe_allow_html=True)
                
    else:
        st.warning("AI 暫時無法分析此物品，請檢查名稱是否正確或稍後再試。")

# Footer
st.markdown("---")
st.caption("Powered by Google Gemini AI • Built with Streamlit")