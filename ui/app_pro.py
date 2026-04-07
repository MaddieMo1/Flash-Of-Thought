import streamlit as st
import requests
import json
import os
import time
import plotly.graph_objects as go
import networkx as nx
import pandas as pd
import numpy as np
from streamlit_mic_recorder import mic_recorder, speech_to_text
from streamlit_echarts import st_echarts
from utils_pro import save_analysis_result

# Backend API URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
API_SESSION = requests.Session()
API_SESSION.trust_env = False

def api_request(method, path, **kwargs):
    kwargs.setdefault("timeout", 60)
    return API_SESSION.request(method, f"{API_BASE_URL}{path}", **kwargs)

st.set_page_config(
    page_title="FlashOfThought Pro",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Pro Max UI/UX (Dark, Cyan/Blue Highlights, Glassmorphism, Premium)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #000000 !important; /* Deep black like Vercel/Linear */
        color: #EDEDED;
    }

    /* Base app container */
    .main .block-container {
        max-width: 1040px;
        padding-top: 4rem;
        padding-bottom: 4rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    /* Text styles */
    h1 {
        font-weight: 700;
        letter-spacing: -0.04em;
        color: #FFFFFF !important;
    }

    h2, h3, h4, h5 {
        font-weight: 600;
        letter-spacing: -0.02em;
        color: #FAFAFA !important;
    }

    p, span, div {
        color: #A1A1AA;
    }

    strong {
        color: #EDEDED;
        font-weight: 600;
    }

    /* Highlight gradient text */
    .highlight-text {
        background: linear-gradient(135deg, #00E5FF 0%, #007AFF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
    }

    /* Cards & Containers (Glassmorphism) */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 4px 24px -1px rgba(0, 0, 0, 0.2) !important;
        transition: border-color 0.3s ease;
    }

    div[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
        border-color: rgba(255, 255, 255, 0.12) !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: #EDEDED;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.06);
        border-color: rgba(255, 255, 255, 0.15);
        color: #FFFFFF;
    }

    /* Primary Button */
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #00E5FF 0%, #007AFF 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 0 16px rgba(0, 122, 255, 0.3) !important;
        border-radius: 8px !important;
        font-weight: 600;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        box-shadow: 0 0 24px rgba(0, 229, 255, 0.5) !important;
        transform: translateY(-1px);
    }

    /* Inputs */
    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
        background-color: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
        color: #EDEDED !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox > div > div:focus-within {
        border-color: #00E5FF !important;
        box-shadow: 0 0 0 1px rgba(0, 229, 255, 0.3) !important;
        background-color: rgba(255, 255, 255, 0.04) !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 1rem;
        padding-bottom: 1rem;
        color: #888888;
        font-weight: 500;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        color: #00E5FF !important;
        border-bottom: 2px solid #00E5FF !important;
        background: transparent !important;
    }

    /* Expanders */
    .stExpander {
        background-color: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 10px !important;
        overflow: hidden;
    }
    .stExpander summary {
        color: #EDEDED !important;
        font-weight: 500 !important;
        background-color: rgba(255,255,255,0.01) !important;
    }
    .stExpander summary:hover {
        color: #00E5FF !important;
        background-color: rgba(255,255,255,0.03) !important;
    }

    /* Alerts / Info boxes */
    div[data-testid="stAlertContainer"] {
        background: rgba(0, 229, 255, 0.03) !important;
        border: 1px solid rgba(0, 229, 255, 0.1) !important;
        border-radius: 8px !important;
        color: #A1A1AA !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 4px;
        height: 4px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.2);
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #00E5FF !important;
        font-weight: 600 !important;
    }

    /* Divider */
    hr {
        border-color: rgba(255,255,255,0.05) !important;
    }
    
    code {
        color: #00E5FF !important;
        background-color: rgba(0, 229, 255, 0.05) !important;
        border-radius: 6px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        border: 1px solid rgba(0, 229, 255, 0.1);
        padding: 0.2em 0.4em;
    }

    .stToast {
        background: rgba(10, 10, 10, 0.95) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        color: #FFFFFF !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='highlight-text'>FlashOfThought Pro</h1>", unsafe_allow_html=True)
st.caption("AI 驱动的灵感捕捉与知识引擎")

# Sidebar for navigation
with st.sidebar:
    st.markdown("<h2 class='highlight-text'>FOT Pro</h2>", unsafe_allow_html=True)
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # Page Option Mapping
    page_options = {
        "record_idea": "💡 捕捉灵感",
        "knowledge_review": "📚 知识库",
        "knowledge_graph": "🌌 神经图谱"
    }
    
    page_selection = st.radio(
        "导航", 
        options=list(page_options.keys()), 
        format_func=lambda x: page_options[x],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.caption("v1.0.0 | Pro Max 设计")

def process_audio(audio_data, file_name, file_type="audio/mp3"):
    """
    Handle audio processing: Upload -> Transcribe -> Structure -> Display
    """
    with st.spinner("神经引擎正在处理音频..."):
        try:
            # 1. Upload
            files = {"file": (file_name, audio_data, file_type)}
            upload_res = api_request("POST", "/upload", files=files)
            
            if upload_res.status_code == 200:
                upload_data = upload_res.json()
                raw_text = upload_data.get("raw_text", "")
                file_url = upload_data.get("file_url", "")
                
                st.toast("转写完成", icon="✓")
                
                # 2. Structure
                with st.spinner("正在结构化思维向量..."):
                    process_res = api_request(
                        "POST",
                        "/process",
                        json={"raw_text": raw_text}
                    )
                    
                    if process_res.status_code == 200:
                        st.session_state.current_note = process_res.json()
                        st.session_state.current_raw_text = raw_text
                        st.session_state.current_file_url = file_url
                        st.rerun()
                    else:
                        st.error(f"结构化失败: {process_res.text}")
            else:
                st.error(f"上传失败: {upload_res.text}")
        except Exception as e:
            st.error(f"发生错误: {str(e)}")

def process_text_input(text):
    """
    Handle text input processing: Structure -> Display -> Save
    """
    if not text.strip():
        st.warning("请输入内容。")
        return

    with st.spinner("正在结构化思维向量..."):
        try:
            process_res = api_request(
                "POST",
                "/process",
                json={"raw_text": text}
            )
            
            if process_res.status_code == 200:
                st.session_state.current_note = process_res.json()
                st.session_state.current_raw_text = text
                st.session_state.current_file_url = ""
                st.toast("结构化成功", icon="✓")
                st.rerun()
            else:
                st.error(f"结构化失败: {process_res.text}")
        except Exception as e:
            st.error(f"发生错误: {str(e)}")

def get_related_notes(query, current_id=None):
    """
    Fetch related notes using semantic search
    """
    try:
        search_res = api_request("POST", "/search", json={"query": query, "limit": 4})
        if search_res.status_code == 200:
            results = search_res.json()
            if current_id:
                results = [r for r in results if r.get('id') != current_id]
            return results[:3] 
    except:
        pass
    return []

def display_note():
    """
    Display the structured note and save button from session state
    """
    if "current_note" not in st.session_state or not st.session_state.current_note:
        return

    note_data = st.session_state.current_note
    raw_text = st.session_state.current_raw_text
    file_url = st.session_state.current_file_url

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    col_main, col_sidebar = st.columns([2.5, 1])

    with col_main:
        with st.container(border=True):
            st.subheader(f"{note_data.get('title', '无标题')}")
            
            # Enhanced Tags Display
            tags = note_data.get('tags', [])
            if tags:
                st.markdown(" ".join([f"`{t}`" for t in tags]))
            
            st.markdown("#### 核心摘要")
            st.info(note_data.get('summary', '暂无摘要。'))
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 核心观点")
                for item in note_data.get('core_ideas', []):
                    st.markdown(f"- {item}")
                
                st.markdown("#### 关键功能")
                for item in note_data.get('key_features', []):
                    st.markdown(f"- {item}")
            
            with col2:
                st.markdown("#### 可能应用")
                for item in note_data.get('possible_applications', []):
                    st.markdown(f"- {item}")
            
            with st.expander("查看原始文本"):
                st.text_area("Raw", value=raw_text, height=100, disabled=True, label_visibility="collapsed")

    with col_sidebar:
        st.markdown("#### 神经元关联")
        related = get_related_notes(note_data.get('summary', '') + " " + note_data.get('title', ''))
        if related:
            st.success("发现关联：")
            for r in related:
                meta = r.get('metadata', {})
                with st.expander(f"{meta.get('title', '无标题')}"):
                    st.caption(f"相关度: {r.get('score', 0):.2f}")
                    st.write(meta.get('summary', ''))
        else:
            st.info("未发现直接关联。这是一个独特的想法。")
    
    # 3. Save
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    col_save, col_clear, _ = st.columns([1, 1, 3])
    with col_save:
        if st.button("保存到知识库", type="primary", use_container_width=True):
            with st.spinner("正在写入记忆..."):
                try:
                    save_payload = {
                        "note": note_data,
                        "raw_text": raw_text,
                        "source_url": file_url
                    }
                    save_res = api_request("POST", "/save", json=save_payload)
                    if save_res.status_code == 200:
                        st.toast("写入成功", icon="✓")
                        st.session_state.current_note = None
                        st.session_state.current_raw_text = ""
                        st.session_state.current_file_url = ""
                        time.sleep(0.5) 
                        st.rerun() 
                    else:
                        st.error(f"保存失败: {save_res.text}")
                except Exception as e:
                    st.error(f"连接错误: {str(e)}")
    
    with col_clear:
        if st.button("放弃", use_container_width=True):
            st.session_state.current_note = None
            st.session_state.current_raw_text = ""
            st.session_state.current_file_url = ""
            st.rerun()

if page_selection == "record_idea":
    st.header("捕捉灵感")
    
    # Always try to display current note if exists
    display_note()
    
    if "current_note" not in st.session_state or not st.session_state.current_note:
        tab1, tab2, tab3, tab4 = st.tabs(["音频上传", "麦克风录音", "文本输入", "快捷指令"])
    
        with tab1:
            audio_file = st.file_uploader("拖拽音频文件到此处", type=['mp3', 'wav', 'm4a', 'aac'])
            if audio_file:
                st.audio(audio_file)
                if st.button("处理音频", type="primary"):
                    process_audio(audio_file, audio_file.name)
                    st.rerun()

        with tab2:
            st.info("点击下方麦克风开始录制你的想法。")
            
            if 'audio_key' not in st.session_state:
                st.session_state.audio_key = 0

            audio_input = st.audio_input("录音", key=f"audio_input_{st.session_state.audio_key}")
            
            if audio_input:
                col_process, col_rerecord = st.columns([1, 1])
                
                with col_process:
                    if st.button("处理录音", type="primary"):
                        timestamp = int(time.time())
                        filename = f"recording_{timestamp}.wav"
                        process_audio(audio_input, filename, "audio/wav")
                        st.rerun()
                
                with col_rerecord:
                    if st.button("重新录制"):
                        st.session_state.audio_key += 1
                        st.rerun()

        with tab3:
            st.markdown("输入纯文本想法，AI 将自动对其进行结构化处理。")
            if "text_input_val" not in st.session_state:
                st.session_state.text_input_val = ""
                
            text_input = st.text_area("Input...", value=st.session_state.text_input_val, height=200, key="idea_text_area", label_visibility="collapsed")
            
            if st.button("结构化文本", type="primary"):
                if "text_input_val" in st.session_state:
                     st.session_state.text_input_val = ""
                process_text_input(text_input)

        with tab4:
            st.markdown("#### 快捷指令模式")
            st.info("说 '闪念...' 接着说出你的想法。")
            
            audio = mic_recorder(
                start_prompt="开始录音",
                stop_prompt="停止并发送",
                key='audio_command',
                format="wav",
                use_container_width=True
            )
            
            if audio:
                st.toast("正在分析指令...", icon="⚙️")
                
                try:
                    files = {"file": ("command.wav", audio['bytes'], "audio/wav")}
                    upload_res = api_request("POST", "/upload", files=files)
                    
                    if upload_res.status_code == 200:
                        upload_data = upload_res.json()
                        text = upload_data.get("raw_text", "")
                        
                        st.success(f"识别结果: {text}")
                        
                        # Command parsing logic
                        if text.startswith("闪念") or text.startswith("记录") or "闪念" in text[:10] or "record" in text.lower():
                            content = text.replace("闪念", "", 1).replace("记录", "", 1).replace("record", "", 1).strip()
                            import re
                            content = re.sub(r'^[，,。.]+', '', content).strip()
                            
                            if content:
                                st.toast("处理中...", icon="⚙️")
                                process_text_input(content)
                            else:
                                st.warning("指令内容为空。")
                        else:
                             st.warning("未检测到触发词，但仍将继续处理。")
                             if len(text) > 1:
                                 process_text_input(text)
                    else:
                        st.error("语音识别失败。")
                except Exception as e:
                    st.error(f"处理错误: {str(e)}")

elif page_selection == "knowledge_review":
    st.header("知识库")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    tab_search, tab_chat, tab_summary = st.tabs(["搜索", "对话", "洞察"])

    with tab_summary:
        st.subheader("AI 洞察")
        st.caption("自动生成你近期想法的综合报告。")
        
        col_sum_1, col_sum_2 = st.columns([1, 3])
        with col_sum_1:
            days_option = st.selectbox("时间范围", [7, 14, 30], format_func=lambda x: f"最近 {x} 天")
            if st.button("生成报告", type="primary", use_container_width=True):
                with st.spinner("正在合成报告..."):
                    try:
                        res = api_request("POST", "/analyze/weekly_summary", json={"days": days_option})
                        if res.status_code == 200:
                            st.session_state.weekly_summary = res.json()
                        else:
                            st.error("生成失败。")
                    except Exception as e:
                        st.error(f"连接错误: {str(e)}")
        
        with col_sum_2:
            if "weekly_summary" in st.session_state and st.session_state.weekly_summary:
                summary = st.session_state.weekly_summary
                data = summary.get("data", {})
                
                st.markdown(f"### 综合报告 ({summary.get('start_date')} ~ {summary.get('end_date')})")
                st.info(f"**共捕捉到想法数: {data.get('total_count', 0)}**")
                
                st.markdown("#### 主要关注点")
                st.write(data.get('weekly_synthesis', '暂无数据。'))
                
                st.divider()
                
                col_bd1, col_bd2 = st.columns(2)
                with col_bd1:
                    st.markdown("#### 主题分布")
                    topics = data.get('topic_breakdown', [])
                    if topics:
                        for t in topics:
                            st.markdown(f"- **{t.get('topic')}**: {t.get('count')}")
                    else:
                        st.caption("暂无主题数据。")
                        
                with col_bd2:
                    st.markdown("#### 核心亮点")
                    highlights = data.get('key_highlights', [])
                    if highlights:
                        for h in highlights:
                            st.markdown(f"- {h}")
                    else:
                        st.caption("暂无亮点。")
            else:
                st.info("点击生成以创建洞察报告。")

    with tab_search:
        with st.container(border=True):
            st.subheader("语义搜索")
            query = st.text_input("搜索内容", placeholder="例如：我关于 AI 的想法是什么？", label_visibility="collapsed")
            
            if query:
                with st.spinner("正在神经空间中搜索..."):
                    try:
                        search_res = api_request("POST", "/search", json={"query": query, "limit": 5})
                        
                        if search_res.status_code == 200:
                            results = search_res.json()
                            
                            if not results:
                                st.warning("未找到相关想法。")
                            
                            st.markdown("### 结果")
                            for res in results:
                                meta = res.get("metadata", {})
                                score = res.get("score", 0)
                                
                                with st.expander(f"{meta.get('title', '无标题')} (相关度: {score:.2f})"):
                                    st.caption(f"创建时间: {meta.get('created_at', '未知')}")
                                    st.markdown(f"**摘要**: {meta.get('summary', '')}")
                                    st.markdown(f"**标签**: {meta.get('tags', '')}")
                                    st.markdown("---")
                                    st.markdown(res.get("document", ""))
                        else:
                            st.error("搜索失败。")
                    except Exception as e:
                        st.error(f"连接错误: {str(e)}")

    with tab_chat:
        st.subheader("与知识库对话")
        st.caption("查询你的第二大脑。")
        
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "context" in msg:
                    with st.expander("参考来源"):
                        for note in msg["context"]:
                            meta = note.get('metadata', {})
                            st.markdown(f"- **{meta.get('title')}**: {meta.get('summary')}")

        if prompt := st.chat_input("询问关于你的笔记..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    try:
                        res = api_request("POST", "/chat", json={"query": prompt})
                        if res.status_code == 200:
                            data = res.json()
                            answer = data.get("answer", "我不知道如何回答。")
                            context = data.get("context", [])
                            
                            st.markdown(answer)
                            if context:
                                with st.expander("参考来源"):
                                    for note in context:
                                        meta = note.get('metadata', {})
                                        st.markdown(f"- **{meta.get('title')}**: {meta.get('summary')}")
                            
                            st.session_state.chat_history.append({
                                "role": "assistant", 
                                "content": answer,
                                "context": context
                            })
                        else:
                            st.error("AI 服务不可用。")
                    except Exception as e:
                        st.error(f"连接错误: {str(e)}")

    st.divider()

    # Recent Notes Section
    col_header, col_refresh = st.columns([4, 1])
    with col_header:
        st.subheader("近期想法")
    with col_refresh:
        if st.button("刷新", use_container_width=True):
            for k in list(st.session_state.keys()):
                if k.startswith("active_analysis_"):
                    del st.session_state[k]
            st.rerun()

    with st.spinner("加载中..."):
        try:
            list_res = api_request("GET", "/notes", params={"limit": 20})
            if list_res.status_code == 200:
                notes = list_res.json()
                if not notes:
                    st.info("尚未记录任何想法。")
                else:
                    for note in notes:
                        meta = note.get("metadata", {})
                        with st.expander(f"{meta.get('title', '无标题')}"):
                            st.caption(f"创建时间: {meta.get('created_at', '未知')}")
                            
                            if f"edit_mode_{note.get('id')}" not in st.session_state:
                                st.session_state[f"edit_mode_{note.get('id')}"] = False
                                
                            col_btns = st.columns([1, 1, 4])
                            with col_btns[0]:
                                if st.button("删除", key=f"del_{note.get('id')}"):
                                    try:
                                        del_res = api_request("DELETE", f"/notes/{note.get('id')}")
                                        if del_res.status_code == 200:
                                            st.toast("已删除")
                                            time.sleep(0.5)
                                            st.rerun()
                                    except Exception as e:
                                        st.error(str(e))
                            
                            with col_btns[1]:
                                if st.button("编辑", key=f"edit_{note.get('id')}"):
                                    st.session_state[f"edit_mode_{note.get('id')}"] = not st.session_state[f"edit_mode_{note.get('id')}"]
                                    st.rerun()

                            if st.session_state[f"edit_mode_{note.get('id')}"]:
                                with st.form(key=f"form_{note.get('id')}"):
                                    new_title = st.text_input("标题", value=meta.get('title', ''))
                                    new_summary = st.text_area("摘要", value=meta.get('summary', ''))
                                    new_tags = st.text_input("标签 (用逗号分隔)", value=meta.get('tags', ''))
                                    
                                    if st.form_submit_button("保存更改"):
                                        updated_note = {
                                            "title": new_title,
                                            "summary": new_summary,
                                            "core_ideas": [], 
                                            "key_features": [],
                                            "possible_applications": [],
                                            "tags": [t.strip() for t in new_tags.split(',')]
                                        }
                                        try:
                                            upd_res = api_request("PUT", f"/notes/{note.get('id')}", json=updated_note)
                                            if upd_res.status_code == 200:
                                                st.toast("更新成功")
                                                st.session_state[f"edit_mode_{note.get('id')}"] = False
                                                time.sleep(0.5)
                                                st.rerun()
                                            else:
                                                st.error("更新失败")
                                        except Exception as e:
                                            st.error(str(e))
                            else:
                                st.markdown(f"**摘要**: {meta.get('summary', '')}")
                                
                                tags = meta.get('tags', '')
                                if tags:
                                    if isinstance(tags, str):
                                        tags = [t.strip() for t in tags.split(',') if t.strip()]
                                    st.markdown(" ".join([f"`{t}`" for t in tags]))
                                
                                st.divider()
                                
                                col_an1, col_an2, col_an3 = st.columns(3)
                                
                                if f"analysis_cache_{note.get('id')}" not in st.session_state:
                                    st.session_state[f"analysis_cache_{note.get('id')}"] = {}
                                
                                if 'expanded_idea' in meta:
                                    st.session_state[f"analysis_cache_{note.get('id')}"]["expand"] = meta['expanded_idea']
                                if 'roadmap' in meta:
                                    st.session_state[f"analysis_cache_{note.get('id')}"]["roadmap"] = meta['roadmap']
                                if 'score' in meta:
                                    st.session_state[f"analysis_cache_{note.get('id')}"]["score"] = meta['score']

                                clicked_action = None

                                with col_an1:
                                    has_expanded = "expand" in st.session_state[f"analysis_cache_{note.get('id')}"]
                                    btn_label = "查看扩展" if has_expanded else "扩展想法"
                                    if st.button(btn_label, key=f"exp_{note.get('id')}"):
                                        clicked_action = "expand"
                                
                                with col_an2:
                                    has_roadmap = "roadmap" in st.session_state[f"analysis_cache_{note.get('id')}"]
                                    btn_label = "查看路线图" if has_roadmap else "生成路线图"
                                    if st.button(btn_label, key=f"road_{note.get('id')}"):
                                        clicked_action = "roadmap"
                                
                                with col_an3:
                                    has_score = "score" in st.session_state[f"analysis_cache_{note.get('id')}"]
                                    btn_label = "查看评分" if has_score else "为想法评分"
                                    if st.button(btn_label, key=f"score_{note.get('id')}"):
                                        clicked_action = "score"

                                active_key = f"active_analysis_{note.get('id')}"
                                cache_key = f"analysis_cache_{note.get('id')}"

                                if clicked_action:
                                    if st.session_state.get(active_key) == clicked_action:
                                        st.session_state.pop(active_key, None)
                                    else:
                                        st.session_state[active_key] = clicked_action

                                analysis_slot = st.empty()

                                active_type = st.session_state.get(active_key)
                                cache = st.session_state.get(cache_key, {})

                                if active_type and active_type not in cache:
                                    analysis_slot.empty()
                                    if active_type == "expand":
                                        with analysis_slot.container():
                                            with st.spinner("正在扩展..."):
                                                try:
                                                    res = api_request("POST", "/analyze/expand", json={"raw_text": note.get("document", "")})
                                                    if res.status_code == 200:
                                                        result_data = res.json()
                                                        st.session_state[cache_key]["expand"] = result_data
                                                        save_analysis_result(note.get('id'), note, 'expand', result_data)
                                                    else:
                                                        st.error("失败")
                                                except Exception as e:
                                                    st.error(str(e))
                                    elif active_type == "roadmap":
                                        with analysis_slot.container():
                                            with st.spinner("正在规划..."):
                                                try:
                                                    res = api_request("POST", "/analyze/roadmap", json={"raw_text": note.get("document", "")})
                                                    if res.status_code == 200:
                                                        result_data = res.json()
                                                        st.session_state[cache_key]["roadmap"] = result_data
                                                        save_analysis_result(note.get('id'), note, 'roadmap', result_data)
                                                    else:
                                                        st.error("失败")
                                                except Exception as e:
                                                    st.error(str(e))
                                    elif active_type == "score":
                                        with analysis_slot.container():
                                            with st.spinner("正在评分..."):
                                                try:
                                                    res = api_request("POST", "/analyze/score", json={"raw_text": note.get("document", "")})
                                                    if res.status_code == 200:
                                                        result_data = res.json()
                                                        st.session_state[cache_key]["score"] = result_data
                                                        save_analysis_result(note.get('id'), note, 'score', result_data)
                                                    else:
                                                        st.error("失败")
                                                except Exception as e:
                                                    st.error(str(e))
                                    cache = st.session_state.get(cache_key, {})
                                
                                if active_type and active_type in cache:
                                    data = cache[active_type]
                                    with analysis_slot.container():
                                        with st.container(border=True):
                                            
                                            if active_type == 'score':
                                                st.caption(f"分析结果: 评分")
                                                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                                                col_s1.metric("创新性", f"{data.get('innovation')}/5")
                                                col_s2.metric("商业性", f"{data.get('business_value')}/5")
                                                col_s3.metric("技术性", f"{data.get('tech_difficulty')}/5")
                                                col_s4.metric("可行性", f"{data.get('feasibility')}/5")
                                                
                                                reason_text = data.get('reason', '')
                                                for marker in ["\n- ", "\n•", "\n* ", "\n1.", "\n2.", "\n3."]:
                                                    idx = reason_text.find(marker)
                                                    if idx != -1:
                                                        reason_text = reason_text[:idx].strip()
                                                        break
                                                st.info(f"理由: {reason_text}")

                                            elif active_type == 'expand':
                                                st.caption(f"分析结果: 扩展")
                                                st.markdown("#### 建议")
                                                st.markdown("**1. 功能**:")
                                                for f in data.get('features', []):
                                                    st.markdown(f"- {f}")
                                                st.markdown(f"**2. 产品形态**: {data.get('product_form')}")
                                                st.markdown(f"**3. 商业模式**: {data.get('business_model')}")
                                                st.markdown(f"**4. 技术实现**: {data.get('tech_implementation')}")
                                                    
                                            elif active_type == 'roadmap':
                                                st.caption(f"分析结果: 路线图")
                                                for phase in data.get('roadmap', []):
                                                    st.markdown(f"**{phase.get('phase', '阶段')}**")
                                                    for task in phase.get('tasks', []):
                                                        st.markdown(f"- [ ] {task}")

                                st.divider()

                                with st.container(border=True):
                                    st.caption("详情")
                                    document_text = note.get("document", "")
                                    
                                    sections = {
                                        "Core Ideas": "核心概念",
                                        "Key Features": "关键功能",
                                        "Applications": "应用场景",
                                        "Raw": "原始文档"
                                    }
                                    
                                    for key, label in sections.items():
                                        start_marker = f"{key}: "
                                        if start_marker in document_text:
                                            start_idx = document_text.find(start_marker) + len(start_marker)
                                            content_end = len(document_text)
                                            
                                            for next_key in ["Title:", "Summary:", "Core Ideas:", "Key Features:", "Applications:", "Raw:"]:
                                                if next_key.strip() == key.strip() + ":":
                                                    continue
                                                next_marker = f"\n{next_key}" 
                                                next_idx = document_text.find(next_marker, start_idx)
                                                if next_idx != -1 and next_idx < content_end:
                                                    content_end = next_idx
                                            
                                            section_content = document_text[start_idx:content_end].strip()
                                            
                                            if section_content and key == "Raw":
                                                with st.expander("原始文本"):
                                                    st.text(section_content)
                                            elif section_content:
                                                st.markdown(f"**{label}**")
                                                if "," in section_content:
                                                    for item in section_content.split(","):
                                                        if item.strip():
                                                            st.markdown(f"- {item.strip()}")
                                                else:
                                                    st.markdown(section_content)
                                                st.write("") 
            else:
                 st.error("加载笔记失败。")
        except Exception as e:
            st.error(f"连接错误: {str(e)}")

elif page_selection == "knowledge_graph":
    st.header("神经图谱")
    st.caption("探索你知识库中的深层联系。")

    with st.spinner("正在渲染图谱..."):
        try:
            res = api_request("GET", "/graph")
            if res.status_code != 200:
                st.error("获取图谱失败。")
                raise RuntimeError("graph api failed")
            
            res.encoding = 'utf-8'
            data = res.json()
            nodes_data = data.get("nodes", [])
            edges_data = data.get("edges", [])

            if not nodes_data:
                st.info("暂无数据。")
            else:
                col_controls = st.columns([1, 1, 1, 3])
                with col_controls[0]:
                    layout_type = st.selectbox("布局", ["force", "circular"], format_func=lambda x: "力导向图" if x == "force" else "环形布局")
                with col_controls[1]:
                    show_labels = st.toggle("显示标签", value=True)
                with col_controls[2]:
                    repulsion = st.slider("排斥力", 100, 2000, 1000) if layout_type == "force" else None

                echart_nodes = []
                for node in nodes_data:
                    group = node.get("group", "level3")
                    label = node.get("label", "")
                    
                    symbol_size = 15
                    category = "其他"
                    if group == "level1":
                        symbol_size = 50
                        category = "核心"
                    elif group == "level2":
                        symbol_size = 20 
                        category = "笔记"
                    else:
                        symbol_size = 12 
                        category = "标签"

                    item_color = node.get("color", "#00E5FF")
                    if item_color == "#A0E0FF": # Change default color to fit new theme
                        item_color = "#00E5FF"

                    tooltip_title = node.get("full_title") or label
                    tooltip_desc = node.get("summary", "")
                    
                    echart_nodes.append({
                        "id": node.get("id"),
                        "name": label,
                        "symbolSize": symbol_size,
                        "value": symbol_size,
                        "category": category,
                        "itemStyle": {
                            "color": item_color,
                            "borderColor": "#000000",
                            "borderWidth": 2 if group != "level3" else 0,
                            "shadowBlur": 16 if group != "level3" else 0,
                            "shadowColor": item_color
                        },
                        "label": {
                            "show": show_labels if group != "level1" else True,
                            "position": "right" if layout_type == "force" else "top",
                            "color": "#EDEDED"
                        },
                        "tooltip": {
                            "formatter": f"<b>{tooltip_title}</b><br/>{tooltip_desc}"
                        }
                    })

                categories = [
                    {"name": "核心"},
                    {"name": "标签"},
                    {"name": "笔记"}
                ]

                echart_edges = []
                for edge in edges_data:
                    echart_edges.append({
                        "source": edge.get("source"),
                        "target": edge.get("target"),
                        "lineStyle": {
                            "width": 1,
                            "curveness": 0.3,
                            "opacity": 0.3,
                            "color": "#ffffff"
                        }
                    })

                option = {
                    "backgroundColor": "transparent",
                    "tooltip": {
                        "trigger": "item",
                        "enterable": True,
                        "backgroundColor": "rgba(10, 10, 10, 0.9)",
                        "borderColor": "rgba(255, 255, 255, 0.1)",
                        "textStyle": {
                            "color": "#EDEDED"
                        }
                    },
                    "legend": {
                        "data": ["核心", "标签", "笔记"],
                        "textStyle": {"color": "#A1A1AA"},
                        "top": "bottom"
                    },
                    "series": [
                        {
                            "type": "graph",
                            "layout": layout_type,
                            "data": echart_nodes,
                            "links": echart_edges,
                            "categories": categories,
                            "roam": True,
                            "label": {
                                "show": show_labels,
                                "position": "right",
                                "formatter": "{b}"
                            },
                            "lineStyle": {
                                "color": "source",
                                "curveness": 0.3
                            },
                            "emphasis": {
                                "focus": "adjacency",
                                "lineStyle": {
                                    "width": 3,
                                    "opacity": 0.8
                                }
                            },
                            "force": {
                                "repulsion": repulsion if layout_type == "force" else 1000,
                                "edgeLength": [50, 200],
                                "gravity": 0.1
                            },
                            "circular": {
                                "rotateLabel": True
                            }
                        }
                    ]
                }

                st_echarts(options=option, height="700px", theme="dark")
                
                st.caption("提示：滚动缩放 | 拖拽平移 | 点击节点高亮连接 | 悬停查看详情")

        except Exception as e:
            st.error(f"加载图谱失败: {str(e)}")
