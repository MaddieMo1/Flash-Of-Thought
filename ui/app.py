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
from ui.utils import save_analysis_result
# from streamlit_agraph import agraph, Node, Edge, Config # Replaced with PyDeck for 3D

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None

# Backend API URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(
    page_title="IdeaPills 💊",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Global Styles */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Typography */
    h1 {
        color: #00D4FF !important; /* Tech Cyan */
        font-family: 'Inter', 'Segoe UI', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    h2, h3 {
        color: #E0E0E0 !important;
        font-family: 'Inter', 'Segoe UI', sans-serif;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 8px; /* Slightly rounded, not pill */
        font-weight: 600;
        border: 1px solid #333;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        border-color: #00D4FF;
        color: #00D4FF;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.2);
    }
    
    /* Containers & Cards */
    .stExpander {
        border: 1px solid #333;
        border-radius: 8px;
        background-color: #1E212B; /* Darker card bg */
    }
    
    /* Inputs */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px;
        background-color: #0E1117;
        border: 1px solid #333;
        color: #FAFAFA;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #00D4FF;
        box-shadow: 0 0 5px rgba(0, 212, 255, 0.3);
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0E1117; 
    }
    ::-webkit-scrollbar-thumb {
        background: #333; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #555; 
    }
    
    /* Tags (Code blocks) */
    code {
        color: #00D4FF !important;
        background-color: rgba(0, 212, 255, 0.1) !important;
        border-radius: 4px;
        font-family: 'Consolas', 'Monaco', monospace;
        border: 1px solid rgba(0, 212, 255, 0.2);
    }
    
    /* Toast */
    .stToast {
        background-color: #1E212B !important;
        border: 1px solid #333;
        color: #FAFAFA !important;
    }
    
    /* Primary Button Override */
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #00D4FF !important;
        color: #0E1117 !important; /* Dark text for contrast */
        border: none;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #00B8E6 !important;
        color: #0E1117 !important;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.4);
    }
    
    /* Divider */
    hr {
        border-color: #333 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("IdeaPills 💊 : 语音想法助手")

# Sidebar for navigation
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/pill.png", width=50)
    st.markdown("### 功能导航")
    
    # Page Option Mapping
    page_options = {
        "record_idea": "🎙️ 录入想法",
        "knowledge_review": "🔍 知识回顾",
        "knowledge_graph": "🕸️ 知识图谱"
    }
    
    page_selection = st.radio(
        "选择模式", 
        options=list(page_options.keys()), 
        format_func=lambda x: page_options[x],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.caption("v0.1.0 | 由 Trae 驱动")

def process_audio(audio_data, file_name, file_type="audio/mp3"):
    """
    Handle audio processing: Upload -> Transcribe -> Structure -> Display
    """
    with st.spinner("🚀 正在上传并转写音频..."):
        try:
            # 1. Upload
            files = {"file": (file_name, audio_data, file_type)}
            upload_res = requests.post(f"{API_BASE_URL}/upload", files=files)
            
            if upload_res.status_code == 200:
                upload_data = upload_res.json()
                raw_text = upload_data.get("raw_text", "")
                file_url = upload_data.get("file_url", "")
                
                st.toast("✅ 转写完成!", icon="🎉")
                
                # 2. Structure
                with st.spinner("🧠 正在整理笔记结构..."):
                    process_res = requests.post(
                        f"{API_BASE_URL}/process", 
                        json={"raw_text": raw_text}
                    )
                    
                    if process_res.status_code == 200:
                        st.session_state.current_note = process_res.json()
                        st.session_state.current_raw_text = raw_text
                        st.session_state.current_file_url = file_url
                    else:
                        st.error(f"整理失败: {process_res.text}")
            else:
                st.error(f"上传失败: {upload_res.text}")
        except Exception as e:
            st.error(f"发生错误: {str(e)}")

def process_text_input(text):
    """
    Handle text input processing: Structure -> Display -> Save
    """
    if not text.strip():
        st.warning("请输入内容")
        return

    with st.spinner("🧠 正在整理笔记结构..."):
        try:
            process_res = requests.post(
                f"{API_BASE_URL}/process", 
                json={"raw_text": text}
            )
            
            if process_res.status_code == 200:
                st.session_state.current_note = process_res.json()
                st.session_state.current_raw_text = text
                st.session_state.current_file_url = ""
            else:
                st.error(f"整理失败: {process_res.text}")
        except Exception as e:
            st.error(f"发生错误: {str(e)}")

def get_related_notes(query, current_id=None):
    """
    Fetch related notes using semantic search
    """
    try:
        search_res = requests.post(f"{API_BASE_URL}/search", json={"query": query, "limit": 4})
        if search_res.status_code == 200:
            results = search_res.json()
            # Filter out the current note itself if current_id is provided
            if current_id:
                results = [r for r in results if r.get('id') != current_id]
            return results[:3] # Return top 3 unique related notes
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

    st.divider()
    
    col_main, col_sidebar = st.columns([2, 1])

    with col_main:
        with st.container(border=True):
            st.subheader(f"📝 {note_data.get('title', '无标题')}")
            
            # Enhanced Tags Display
            tags = note_data.get('tags', [])
            if tags:
                st.markdown(" ".join([f"`#{t}`" for t in tags]))
            
            st.markdown("### 💡 核心摘要")
            st.info(note_data.get('summary', '暂无摘要'))
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🎯 核心观点")
                for item in note_data.get('core_ideas', []):
                    st.markdown(f"- {item}")
                
                st.markdown("### 🛠️ 关键功能")
                for item in note_data.get('key_features', []):
                    st.markdown(f"- {item}")
            
            with col2:
                st.markdown("### 🚀 可能应用")
                for item in note_data.get('possible_applications', []):
                    st.markdown(f"- {item}")
            
            with st.expander("查看原始文本"):
                st.text_area("原始文本", value=raw_text, height=100, disabled=True)

    with col_sidebar:
        st.markdown("### 🧠 第二大脑关联")
        related = get_related_notes(note_data.get('summary', '') + " " + note_data.get('title', ''))
        if related:
            st.success("发现相关想法：")
            for r in related:
                meta = r.get('metadata', {})
                with st.expander(f"🔗 {meta.get('title', '无标题')}"):
                    st.caption(f"相似度: {r.get('score', 0):.2f}")
                    st.write(meta.get('summary', ''))
        else:
            st.info("暂无直接关联的想法，继续记录以构建你的知识图谱！")
    
    # 3. Save
    st.write("")
    col_save, col_clear, _ = st.columns([1, 1, 3])
    with col_save:
        if st.button("💾 保存到知识库", type="primary", use_container_width=True):
            with st.spinner("正在保存..."):
                try:
                    save_payload = {
                        "note": note_data,
                        "raw_text": raw_text,
                        "source_url": file_url
                    }
                    save_res = requests.post(f"{API_BASE_URL}/save", json=save_payload)
                    if save_res.status_code == 200:
                        st.balloons()
                        st.toast("保存成功!", icon="💾")
                        # Clear current note
                        st.session_state.current_note = None
                        st.session_state.current_raw_text = ""
                        st.session_state.current_file_url = ""
                        time.sleep(1) 
                        st.rerun() 
                    else:
                        st.error(f"保存失败: {save_res.text}")
                except Exception as e:
                    st.error(f"连接失败: {str(e)}")
    
    with col_clear:
        if st.button("🗑️ 放弃并清除", use_container_width=False):
            st.session_state.current_note = None
            st.session_state.current_raw_text = ""
            st.session_state.current_file_url = ""
            st.rerun()

if page_selection == "record_idea":
    st.header("记录你的灵感")
    
    # Always try to display current note if exists
    display_note()
    
    if "current_note" not in st.session_state or not st.session_state.current_note:
        tab1, tab2, tab3, tab4 = st.tabs(["📤 上传文件", "🎤 麦克风录音", "📝 文字输入", "⚡ 语音指令"])
    
        with tab1:
            audio_file = st.file_uploader("拖拽或选择音频文件", type=['mp3', 'wav', 'm4a', 'aac'])
            if audio_file:
                st.audio(audio_file)
                if st.button("开始处理 (文件)", type="primary"):
                    process_audio(audio_file, audio_file.name)
                    st.rerun()

        with tab2:
            st.info("请点击下方麦克风按钮开始录音")
            
            # Initialize session state for audio key if not exists
            if 'audio_key' not in st.session_state:
                st.session_state.audio_key = 0

            # Audio Input with dynamic key
            audio_input = st.audio_input("录制语音", key=f"audio_input_{st.session_state.audio_key}")
            
            if audio_input:
                col_process, col_rerecord = st.columns([1, 1])
                
                with col_process:
                    if st.button("开始处理 (录音)", type="primary"):
                        # Generate a filename for the recording
                        timestamp = int(time.time())
                        filename = f"recording_{timestamp}.wav"
                        process_audio(audio_input, filename, "audio/wav")
                        st.rerun()
                
                with col_rerecord:
                    if st.button("🔄 重新录音"):
                        st.session_state.audio_key += 1
                        st.rerun()

        with tab3:
            st.markdown("直接输入文字想法，AI将为您自动整理")
            # Use session state to persist text input, or clear it if needed
            if "text_input_val" not in st.session_state:
                st.session_state.text_input_val = ""
                
            text_input = st.text_area("输入想法...", value=st.session_state.text_input_val, height=200, key="idea_text_area")
            
            if st.button("开始整理 (文字)", type="primary"):
                # Clear previous state
                if "text_input_val" in st.session_state:
                     st.session_state.text_input_val = text_input
                process_text_input(text_input)
                st.rerun()

        with tab4:
            st.markdown("### 🎙️ 闪念指令模式")
            st.info("点击下方按钮开始录音，说完点击停止。尝试说：'闪念，记录一个新的AI想法...'")
            
            # Use mic_recorder instead of speech_to_text for better compatibility
            audio = mic_recorder(
                start_prompt="🔴 点击开始指令 (录音中...)",
                stop_prompt="⏹️ 完成并发送",
                key='audio_command',
                format="wav",
                use_container_width=True
            )
            
            if audio:
                st.toast("正在分析语音指令...", icon="🔄")
                
                try:
                    # Construct file for upload
                    files = {"file": ("command.wav", audio['bytes'], "audio/wav")}
                    
                    # Call upload API (which does ASR)
                    upload_res = requests.post(f"{API_BASE_URL}/upload", files=files)
                    
                    if upload_res.status_code == 200:
                        upload_data = upload_res.json()
                        text = upload_data.get("raw_text", "")
                        
                        st.success(f"识别内容: {text}")
                        
                        # Logic for command parsing
                        # Simple keyword detection
                        if text.startswith("闪念") or text.startswith("记录") or "闪念" in text[:10]:
                            # Extract content
                            content = text.replace("闪念", "", 1).replace("记录", "", 1).strip()
                             # Remove leading punctuation
                            import re
                            content = re.sub(r'^[，,。.]+', '', content).strip()
                            
                            if content:
                                st.toast(f"正在处理: {content[:10]}...", icon="🧠")
                                process_text_input(content)
                                st.rerun()
                            else:
                                st.warning("指令内容为空")
                        else:
                             # Fallback
                             st.warning("未检测到'闪念'，但已为您记录。")
                             if len(text) > 1:
                                 process_text_input(text)
                                 st.rerun()
                    else:
                        st.error(f"语音识别失败: {upload_res.text}")
                except Exception as e:
                    st.error(f"处理出错: {str(e)}")

elif page_selection == "knowledge_review":
    st.header("知识库")
    
    # Chat Review Mode
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    tab_search, tab_chat, tab_summary = st.tabs(["🔎 智能搜索", "💬 聊天回顾", "📊 AI周报"])

    with tab_summary:
        st.subheader("📅 AI灵感周报")
        st.caption("自动生成本周灵感总结，助你复盘思考")
        
        col_sum_1, col_sum_2 = st.columns([1, 3])
        with col_sum_1:
            days_option = st.selectbox("时间范围", [7, 14, 30], format_func=lambda x: f"最近 {x} 天")
            if st.button("✨ 生成周报", type="primary", use_container_width=True):
                with st.spinner("AI正在分析你的灵感..."):
                    try:
                        res = requests.post(f"{API_BASE_URL}/analyze/weekly_summary", json={"days": days_option})
                        if res.status_code == 200:
                            st.session_state.weekly_summary = res.json()
                        else:
                            st.error(f"生成失败: {res.text}")
                    except Exception as e:
                        st.error(f"连接失败: {str(e)}")
        
        with col_sum_2:
            if "weekly_summary" in st.session_state and st.session_state.weekly_summary:
                summary = st.session_state.weekly_summary
                data = summary.get("data", {})
                
                st.markdown(f"### 🗓️ 周报 ({summary.get('start_date')} ~ {summary.get('end_date')})")
                
                # 1. Overview
                st.info(f"**本周共记录 {data.get('total_count', 0)} 条想法**")
                
                st.markdown("#### 🧠 本周关注点")
                st.write(data.get('weekly_synthesis', '暂无总结'))
                
                st.divider()
                
                # 2. Breakdown
                col_bd1, col_bd2 = st.columns(2)
                with col_bd1:
                    st.markdown("#### 🏷️ 主题分布")
                    topics = data.get('topic_breakdown', [])
                    if topics:
                        for t in topics:
                            st.markdown(f"- **{t.get('topic')}**: {t.get('count')}")
                    else:
                        st.caption("暂无分类数据")
                        
                with col_bd2:
                    st.markdown("#### ⭐ 重点想法")
                    highlights = data.get('key_highlights', [])
                    if highlights:
                        for h in highlights:
                            st.markdown(f"- {h}")
                    else:
                        st.caption("暂无重点想法")
            else:
                st.info("👈 点击左侧按钮生成你的灵感周报")

    with tab_search:
        with st.container(border=True):
            st.subheader("🔍 智能搜索")
            query = st.text_input("输入关键词或问题", placeholder="例如：我上次关于AI的计划是什么？")
            
            if query:
                with st.spinner("正在搜索..."):
                    try:
                        search_res = requests.post(f"{API_BASE_URL}/search", json={"query": query, "limit": 5})
                        
                        if search_res.status_code == 200:
                            results = search_res.json()
                            
                            if not results:
                                st.warning("没有找到相关笔记。")
                            
                            st.markdown("### 搜索结果")
                            for res in results:
                                meta = res.get("metadata", {})
                                score = res.get("score", 0)
                                
                                with st.expander(f"📄 {meta.get('title', '无标题')} (相似度: {score:.2f})"):
                                    st.caption(f"📅 创建时间: {meta.get('created_at', '未知')}")
                                    st.markdown(f"**摘要**: {meta.get('summary', '')}")
                                    st.markdown(f"**标签**: {meta.get('tags', '')}")
                                    st.markdown("---")
                                    st.markdown(res.get("document", ""))
                        else:
                            st.error(f"搜索失败: {search_res.text}")
                    except Exception as e:
                        st.error(f"连接失败: {str(e)}")

    with tab_chat:
        st.subheader("💬 与你的知识库对话")
        st.caption("AI将基于你的所有笔记回答问题")
        
        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "context" in msg:
                    with st.expander("📚 参考笔记"):
                        for note in msg["context"]:
                            meta = note.get('metadata', {})
                            st.markdown(f"- **{meta.get('title')}**: {meta.get('summary')}")

        # Chat Input
        if prompt := st.chat_input("问我关于你笔记的问题..."):
            # Add user message
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    try:
                        res = requests.post(f"{API_BASE_URL}/chat", json={"query": prompt})
                        if res.status_code == 200:
                            data = res.json()
                            answer = data.get("answer", "我不知道怎么回答。")
                            context = data.get("context", [])
                            
                            st.markdown(answer)
                            if context:
                                with st.expander("📚 参考笔记"):
                                    for note in context:
                                        meta = note.get('metadata', {})
                                        st.markdown(f"- **{meta.get('title')}**: {meta.get('summary')}")
                            
                            st.session_state.chat_history.append({
                                "role": "assistant", 
                                "content": answer,
                                "context": context
                            })
                        else:
                            st.error("AI服务暂时不可用")
                    except Exception as e:
                        st.error(f"连接错误: {str(e)}")

    st.divider()

    # Recent Notes Section
    col_header, col_refresh = st.columns([4, 1])
    with col_header:
        st.subheader("📚 最近笔记")
    with col_refresh:
        if st.button("🔄 刷新", use_container_width=True):
            # Reset per-note analysis UI state so refresh doesn't look like data disappeared
            for k in list(st.session_state.keys()):
                if k.startswith("active_analysis_"):
                    del st.session_state[k]
            st.rerun()

    with st.spinner("正在加载笔记列表..."):
        try:
            list_res = requests.get(f"{API_BASE_URL}/notes", params={"limit": 20})
            if list_res.status_code == 200:
                notes = list_res.json()
                if not notes:
                    st.info("还没有笔记，快去录入一些想法吧！")
                else:
                    for note in notes:
                        meta = note.get("metadata", {})
                        with st.expander(f"📝 {meta.get('title', '无标题')}"):
                            st.caption(f"📅 创建时间: {meta.get('created_at', '未知')}")
                            
                            # Edit Mode Toggle
                            if f"edit_mode_{note.get('id')}" not in st.session_state:
                                st.session_state[f"edit_mode_{note.get('id')}"] = False
                                
                            col_btns = st.columns([1, 1, 4])
                            with col_btns[0]:
                                if st.button("🗑️ 删除", key=f"del_{note.get('id')}"):
                                    try:
                                        del_res = requests.delete(f"{API_BASE_URL}/notes/{note.get('id')}")
                                        if del_res.status_code == 200:
                                            st.toast("删除成功!")
                                            time.sleep(1)
                                            st.rerun()
                                    except Exception as e:
                                        st.error(str(e))
                            
                            with col_btns[1]:
                                if st.button("✏️ 编辑", key=f"edit_{note.get('id')}"):
                                    st.session_state[f"edit_mode_{note.get('id')}"] = not st.session_state[f"edit_mode_{note.get('id')}"]
                                    st.rerun()

                            if st.session_state[f"edit_mode_{note.get('id')}"]:
                                with st.form(key=f"form_{note.get('id')}"):
                                    new_title = st.text_input("标题", value=meta.get('title', ''))
                                    new_summary = st.text_area("摘要", value=meta.get('summary', ''))
                                    new_tags = st.text_input("标签 (逗号分隔)", value=meta.get('tags', ''))
                                    
                                    # Try to extract core_ideas etc from document if possible, or just leave empty for now
                                    # Since we don't store them in metadata individually, we can't easily edit them without parsing document text
                                    # For MVP, we only support editing title, summary, tags.
                                    
                                    if st.form_submit_button("保存修改"):
                                        updated_note = {
                                            "title": new_title,
                                            "summary": new_summary,
                                            "core_ideas": [], 
                                            "key_features": [],
                                            "possible_applications": [],
                                            "tags": [t.strip() for t in new_tags.split(',')]
                                        }
                                        try:
                                            upd_res = requests.put(f"{API_BASE_URL}/notes/{note.get('id')}", json=updated_note)
                                            if upd_res.status_code == 200:
                                                st.toast("修改成功!")
                                                st.session_state[f"edit_mode_{note.get('id')}"] = False
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error("修改失败")
                                        except Exception as e:
                                            st.error(str(e))
                            else:
                                # Normal Display
                                st.markdown(f"**摘要**: {meta.get('summary', '')}")
                                
                                tags = meta.get('tags', '')
                                if tags:
                                    # Check if it's a list or string
                                    if isinstance(tags, str):
                                        tags = [t.strip() for t in tags.split(',') if t.strip()]
                                    st.markdown(" ".join([f"`#{t}`" for t in tags]))
                                
                                st.divider()
                                
                                # Deep Analysis Buttons
                                col_an1, col_an2, col_an3 = st.columns(3)
                                
                                # Initialize cache structure if not exists
                                if f"analysis_cache_{note.get('id')}" not in st.session_state:
                                    st.session_state[f"analysis_cache_{note.get('id')}"] = {}
                                
                                # Pre-populate cache from persisted metadata
                                if 'expanded_idea' in meta:
                                    st.session_state[f"analysis_cache_{note.get('id')}"]["expand"] = meta['expanded_idea']
                                    # If existing, set active state to show it? No, user has to click button to show it,
                                    # but we shouldn't re-fetch.
                                    # Wait, user wants to see it automatically if it exists?
                                    # "点击扩展想法按钮，还是会重新AI生成，而不是加载上次生成的结果"
                                    # This means the button click logic is not checking the cache correctly or cache is empty.
                                    
                                if 'roadmap' in meta:
                                    st.session_state[f"analysis_cache_{note.get('id')}"]["roadmap"] = meta['roadmap']
                                if 'score' in meta:
                                    st.session_state[f"analysis_cache_{note.get('id')}"]["score"] = meta['score']

                                clicked_action = None

                                with col_an1:
                                    # Check if we have cached data to determine button label or style
                                    has_expanded = "expand" in st.session_state[f"analysis_cache_{note.get('id')}"]
                                    btn_label = "✨ 查看扩展" if has_expanded else "✨ 扩展想法"
                                    
                                    if st.button(btn_label, key=f"exp_{note.get('id')}"):
                                        clicked_action = "expand"
                                
                                with col_an2:
                                    has_roadmap = "roadmap" in st.session_state[f"analysis_cache_{note.get('id')}"]
                                    btn_label = "📅 查看路线" if has_roadmap else "📅 生成路线"
                                    
                                    if st.button(btn_label, key=f"road_{note.get('id')}"):
                                        clicked_action = "roadmap"
                                
                                with col_an3:
                                    has_score = "score" in st.session_state[f"analysis_cache_{note.get('id')}"]
                                    btn_label = "📊 查看评分" if has_score else "📊 灵感评分"
                                    
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
                                            with st.spinner("AI正在扩展想法..."):
                                                try:
                                                    res = requests.post(
                                                        f"{API_BASE_URL}/analyze/expand",
                                                        json={"raw_text": note.get("document", "")},
                                                    )
                                                    if res.status_code == 200:
                                                        result_data = res.json()
                                                        st.session_state[cache_key]["expand"] = result_data
                                                        save_analysis_result(note.get('id'), note, 'expand', result_data)
                                                    else:
                                                        st.error("扩展失败")
                                                except Exception as e:
                                                    st.error(str(e))
                                    elif active_type == "roadmap":
                                        with analysis_slot.container():
                                            with st.spinner("AI正在规划路线..."):
                                                try:
                                                    res = requests.post(
                                                        f"{API_BASE_URL}/analyze/roadmap",
                                                        json={"raw_text": note.get("document", "")},
                                                    )
                                                    if res.status_code == 200:
                                                        result_data = res.json()
                                                        st.session_state[cache_key]["roadmap"] = result_data
                                                        save_analysis_result(note.get('id'), note, 'roadmap', result_data)
                                                    else:
                                                        st.error("生成失败")
                                                except Exception as e:
                                                    st.error(str(e))
                                    elif active_type == "score":
                                        with analysis_slot.container():
                                            with st.spinner("AI正在评分..."):
                                                try:
                                                    res = requests.post(
                                                        f"{API_BASE_URL}/analyze/score",
                                                        json={"raw_text": note.get("document", "")},
                                                    )
                                                    if res.status_code == 200:
                                                        result_data = res.json()
                                                        st.session_state[cache_key]["score"] = result_data
                                                        save_analysis_result(note.get('id'), note, 'score', result_data)
                                                    else:
                                                        st.error("评分失败")
                                                except Exception as e:
                                                    st.error(str(e))
                                    cache = st.session_state.get(cache_key, {})
                                
                                if active_type and active_type in cache:
                                    data = cache[active_type]
                                    with analysis_slot.container():
                                        with st.container(border=True):
                                            st.caption(f"🤖 AI分析: {active_type}")
                                            
                                            if active_type == 'score':
                                                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                                                col_s1.metric("创新性", f"{data.get('innovation')}/5")
                                                col_s2.metric("商业价值", f"{data.get('business_value')}/5")
                                                col_s3.metric("技术难度", f"{data.get('tech_difficulty')}/5")
                                                col_s4.metric("可行性", f"{data.get('feasibility')}/5")
                                                
                                                reason_text = data.get('reason', '')
                                                for marker in ["\n- ", "\n•", "\n* ", "\n1.", "\n2.", "\n3."]:
                                                    idx = reason_text.find(marker)
                                                    if idx != -1:
                                                        reason_text = reason_text[:idx].strip()
                                                        break
                                                st.info(f"💡 理由: {reason_text}")

                                            elif active_type == 'expand':
                                                st.markdown("### 💡 AI扩展建议")
                                                st.markdown("**1. 功能**:")
                                                for f in data.get('features', []):
                                                    st.markdown(f"- {f}")
                                                st.markdown(f"**2. 产品形态**: {data.get('product_form')}")
                                                st.markdown(f"**3. 商业模式**: {data.get('business_model')}")
                                                st.markdown(f"**4. 技术实现**: {data.get('tech_implementation')}")
                                                    
                                            elif active_type == 'roadmap':
                                                for phase in data.get('roadmap', []):
                                                    st.markdown(f"**{phase.get('phase', '阶段')}**")
                                                    for task in phase.get('tasks', []):
                                                        st.markdown(f"- [ ] {task}")

                                st.divider()

                                with st.container(border=True):
                                    st.caption("📌 笔记要点")
                                    
                                    # Try to parse the document content to display it nicely
                                    # The document format is: Title: ...\nSummary: ...\nCore Ideas: ...\nKey Features: ...\nApplications: ...\nRaw: ...
                                    document_text = note.get("document", "")
                                    
                                    # Simple parsing logic (can be improved)
                                    sections = {
                                        "Core Ideas": "🎯 核心观点",
                                        "Key Features": "🛠️ 关键功能",
                                        "Applications": "🚀 可能应用",
                                        "Raw": "📝 原始记录"
                                    }
                                    
                                    for key, label in sections.items():
                                        start_marker = f"{key}: "
                                        if start_marker in document_text:
                                            start_idx = document_text.find(start_marker) + len(start_marker)
                                            content_end = len(document_text)
                                            
                                            # Look for the next section header
                                            for next_key in ["Title:", "Summary:", "Core Ideas:", "Key Features:", "Applications:", "Raw:"]:
                                                # Ensure we don't find the current key itself if it appears later (unlikely but safe)
                                                if next_key.strip() == key.strip() + ":":
                                                    continue
                                                    
                                                next_marker = f"\n{next_key}" 
                                                next_idx = document_text.find(next_marker, start_idx)
                                                if next_idx != -1 and next_idx < content_end:
                                                    content_end = next_idx
                                            
                                            section_content = document_text[start_idx:content_end].strip()
                                            
                                            if section_content and key == "Raw":
                                                with st.expander("查看原始文本"):
                                                    st.text(section_content)
                                            elif section_content:
                                                st.markdown(f"**{label}**")
                                                if "," in section_content:
                                                    for item in section_content.split(","):
                                                        if item.strip():
                                                            st.markdown(f"- {item.strip()}")
                                                else:
                                                    st.markdown(section_content)
                                                st.write("") # Spacer
            else:
                 st.error(f"加载失败: {list_res.text}")
        except Exception as e:
            st.error(f"连接失败: {str(e)}")

elif page_selection == "knowledge_graph":
    st.header("🌌 知识图谱")
    st.caption("探索你的知识星系：核心想法 → 功能分类 → 知识卡片")

    with st.spinner("正在构建知识图谱..."):
        try:
            res = requests.get(f"{API_BASE_URL}/graph")
            if res.status_code != 200:
                st.error(f"获取图谱失败: {res.text}")
                raise RuntimeError("graph api failed")
            
            # Force UTF-8 decoding
            res.encoding = 'utf-8'
            data = res.json()
            nodes_data = data.get("nodes", [])
            edges_data = data.get("edges", [])

            if not nodes_data:
                st.info("暂无数据，请先录入一些想法。")
            else:
                # Layout Control
                col_controls = st.columns([1, 1, 1, 3])
                with col_controls[0]:
                    layout_type = st.selectbox("布局模式", ["force", "circular"], format_func=lambda x: "力导向图" if x == "force" else "环形布局")
                with col_controls[1]:
                    show_labels = st.toggle("显示标签", value=True)
                with col_controls[2]:
                    repulsion = st.slider("排斥力", 100, 2000, 1000) if layout_type == "force" else None

                # Process nodes for ECharts
                echart_nodes = []
                categories = []
                seen_categories = set()

                for node in nodes_data:
                    group = node.get("group", "level3")
                    label = node.get("label", "")
                    category = node.get("category", "其他")
                    
                    # Size mapping
                    symbol_size = 15
                    if group == "level1":
                        symbol_size = 60
                        category = "Core"
                    elif group == "level2":
                        symbol_size = 25 # Note size
                        category = "Note"
                    else:
                        symbol_size = 15 # Tag size
                        category = "Tag"

                    # Color mapping
                    item_color = node.get("color", "#A0E0FF")

                    # Tooltip content
                    tooltip_title = node.get("full_title") or label
                    tooltip_desc = node.get("summary", "")
                    
                    echart_nodes.append({
                        "id": node.get("id"),
                        "name": label,
                        "symbolSize": symbol_size,
                        "value": symbol_size,
                        "category": category, # This is used for legend mapping
                        "itemStyle": {
                            "color": item_color,
                            "borderColor": "#fff",
                            "borderWidth": 1 if group == "level3" else 2,
                            "shadowBlur": 10 if group != "level3" else 0,
                            "shadowColor": item_color
                        },
                        "label": {
                            "show": show_labels if group != "level1" else True,
                            "position": "right" if layout_type == "force" else "top",
                            "color": "#fff"
                        },
                        "tooltip": {
                            "formatter": f"<b>{tooltip_title}</b><br/>{tooltip_desc}"
                        }
                    })

                # Define legend categories
                categories = [
                    {"name": "Core"},
                    {"name": "Tag"},
                    {"name": "Note"}
                ]

                # Process edges
                echart_edges = []
                for edge in edges_data:
                    echart_edges.append({
                        "source": edge.get("source"),
                        "target": edge.get("target"),
                        "lineStyle": {
                            "width": 1,
                            "curveness": 0.3,
                            "opacity": 0.5
                        }
                    })

                # ECharts Option
                option = {
                    "backgroundColor": "#0E1117", # Match Streamlit dark theme
                    "title": {
                        "text": "",
                        "textStyle": {"color": "#fff"}
                    },
                    "tooltip": {
                        "trigger": "item",
                        "enterable": True
                    },
                    "legend": {
                        "data": ["Core", "Tag", "Note"],
                        "textStyle": {"color": "#fff"},
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
                                    "width": 4
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

                # Render Graph
                st_echarts(options=option, height="700px", theme="dark")
                
                # Help text
                st.caption("💡 操作提示：滚轮缩放 | 拖拽移动 | 点击节点高亮连接关系 | 悬停查看详情")

        except Exception as e:
            st.error(f"加载图谱时发生错误: {str(e)}")
