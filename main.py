# SQLite fix for Streamlit deployment
try:
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

import streamlit as st
import time
from datetime import datetime
from rag import process_urls, generate_answer

# Page configuration
st.set_page_config(
    page_title="Docubot - AI Document Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Modern CSS styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Global Styles */
    .main {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }
    
    /* Hide Streamlit elements */
    #MainMenu, header, footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Enhanced Header with glassmorphism */
    .main-header {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 50%, rgba(240, 147, 251, 0.1) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 4rem 2rem;
        border-radius: 24px;
        margin-bottom: 3rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 25px 50px rgba(102, 126, 234, 0.15);
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: conic-gradient(from 0deg at 50% 50%, transparent 0deg, rgba(102, 126, 234, 0.05) 60deg, transparent 120deg);
        animation: rotate 20s linear infinite;
        pointer-events: none;
    }
    
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .main-header h1 {
        font-size: 4rem;
        font-weight: 800;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        position: relative;
        z-index: 2;
        text-shadow: none;
    }
    
    .main-header p {
        font-size: 1.3rem;
        font-weight: 400;
        color: #64748b;
        position: relative;
        z-index: 2;
        margin: 0;
    }
    
    /* Enhanced Cards with better shadows */
    .feature-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        padding: 2.5rem;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        margin: 2rem 0;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.1);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    }
    
    .feature-card:hover {
        transform: translateY(-4px) scale(1.01);
        box-shadow: 0 30px 60px rgba(0, 0, 0, 0.15), 0 5px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Enhanced Sidebar */
    .sidebar .block-container {
        padding-top: 2rem;
    }
    
    .sidebar-section {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        padding: 2rem;
        border-radius: 20px;
        margin: 2rem 0;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }
    
    .sidebar-section:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.12);
    }
    
    /* Enhanced Metrics */
    .metric-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(255, 255, 255, 0.95) 100%);
        backdrop-filter: blur(15px);
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        border: 1px solid rgba(102, 126, 234, 0.1);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
    }
    
    /* Enhanced Status Messages */
    .status-success {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(255, 255, 255, 0.9) 100%);
        backdrop-filter: blur(10px);
        color: #065f46;
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid rgba(16, 185, 129, 0.2);
        box-shadow: 0 10px 25px rgba(16, 185, 129, 0.1);
    }
    
    .status-error {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(255, 255, 255, 0.9) 100%);
        backdrop-filter: blur(10px);
        color: #7f1d1d;
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid rgba(239, 68, 68, 0.2);
        box-shadow: 0 10px 25px rgba(239, 68, 68, 0.1);
    }
    
    /* Enhanced Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 30px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    /* Completely Redesigned Footer */
    .modern-footer {
        background: linear-gradient(135deg, #1e293b 0%, #334155 50%, #475569 100%);
        margin-top: 4rem;
        padding: 0;
        border-radius: 24px 24px 0 0;
        position: relative;
        overflow: hidden;
        box-shadow: 0 -20px 40px rgba(0, 0, 0, 0.1);
    }
    
    .footer-wave {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 60px;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 120" preserveAspectRatio="none"><path d="M0,0V46.29c47.79,22.2,103.59,32.17,158,28,70.36-5.37,136.33-33.31,206.8-37.5C438.64,32.43,512.34,53.67,583,72.05c69.27,18,138.3,24.88,209.4,13.08,36.15-6,69.85-17.84,104.45-29.34C989.49,25,1113-14.29,1200,52.47V0Z" opacity=".25" fill="%23667eea"></path><path d="M0,0V15.81C13,36.92,27.64,56.86,47.69,72.05,99.41,111.27,165,111,224.58,91.58c31.15-10.15,60.09-26.07,89.67-39.8,40.92-19,84.73-46,130.83-49.67,36.26-2.85,70.9,9.42,98.6,31.56,31.77,25.39,62.32,62,103.63,73,40.44,10.79,81.35-6.69,119.13-24.28s75.16-39,116.92-43.05c59.73-5.85,113.28,22.88,168.9,38.84,30.2,8.66,59,6.17,87.09-7.5,22.43-10.89,48-26.93,60.65-49.24V0Z" opacity=".5" fill="%23667eea"></path><path d="M0,0V5.63C149.93,59,314.09,71.32,475.83,42.57c43-7.64,84.23-20.12,127.61-26.46,59-8.63,112.48,12.24,165.56,35.4C827.93,77.22,886,95.24,951.2,90c86.53-7,172.46-45.71,248.8-84.81V0Z" fill="%23667eea"></path></svg>') no-repeat;
        background-size: cover;
        opacity: 0.8;
    }
    
    .footer-content {
        padding: 4rem 2rem 2rem 2rem;
        position: relative;
        z-index: 2;
        color: white;
    }
    
    .footer-grid {
        display: grid;
        grid-template-columns: 2fr 1fr 1fr;
        gap: 3rem;
        align-items: start;
        margin-bottom: 2rem;
    }
    
    .footer-brand-section {
        text-align: left;
    }
    
    .footer-brand {
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .footer-description {
        font-size: 1.1rem;
        line-height: 1.6;
        opacity: 0.9;
        color: #cbd5e1;
        margin-bottom: 1.5rem;
    }
    
    .footer-features {
        display: flex;
        flex-wrap: wrap;
        gap: 0.8rem;
    }
    
    .feature-tag {
        background: rgba(240, 147, 251, 0.2);
        color: #f093fb;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-size: 0.85rem;
        font-weight: 500;
        border: 1px solid rgba(240, 147, 251, 0.3);
        backdrop-filter: blur(5px);
    }
    
    .footer-section h4 {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #f1f5f9;
    }
    
    .footer-links {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .footer-links li {
        margin-bottom: 0.8rem;
    }
    
    .footer-links a {
        color: #cbd5e1;
        text-decoration: none;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .footer-links a:hover {
        color: #f093fb;
        transform: translateX(5px);
    }
    
    .footer-stats {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }
    
    .stat-item {
        text-align: center;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        backdrop-filter: blur(5px);
    }
    
    .stat-number {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f093fb;
        display: block;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: #cbd5e1;
        opacity: 0.8;
    }
    
    .footer-bottom {
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding-top: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1rem;
    }
    
    .footer-copyright {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    
    .footer-social {
        display: flex;
        gap: 1rem;
    }
    
    .social-icon {
        width: 40px;
        height: 40px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #cbd5e1;
        text-decoration: none;
        transition: all 0.3s ease;
        backdrop-filter: blur(5px);
    }
    
    .social-icon:hover {
        background: rgba(240, 147, 251, 0.2);
        color: #f093fb;
        transform: translateY(-2px);
    }
    
    /* Enhanced Animations */
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    .float-animation {
        animation: float 6s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .pulse-animation {
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2.5rem;
        }
        
        .footer-grid {
            grid-template-columns: 1fr;
            gap: 2rem;
            text-align: center;
        }
        
        .footer-brand-section {
            text-align: center;
        }
        
        .footer-bottom {
            flex-direction: column;
            text-align: center;
        }
        
        .footer-stats {
            grid-template-columns: 1fr;
        }
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2, #f093fb);
    }
</style>
""", unsafe_allow_html=True)

# Enhanced header with animation
st.markdown("""
<div class="main-header float-animation">
    <h1>🤖 Docubot</h1>
    <p>Transform any web content into intelligent, searchable knowledge with AI-powered analysis</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'processed_urls' not in st.session_state:
    st.session_state.processed_urls = []
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'url_count' not in st.session_state:
    st.session_state.url_count = 3

# Enhanced Sidebar
with st.sidebar:
    st.markdown("### 🔧 Configuration Panel")
    
    # URL Input Section
    st.markdown("#### 🌐 Document Sources")
    
    # Dynamic URL inputs
    st.markdown("**Add URLs to analyze:**")
    
    # Number of URL inputs with better alignment
    col1, col2 = st.columns([3, 1])
    with col1:
        url_count = st.number_input("Number of URLs", min_value=1, max_value=10, value=st.session_state.url_count, key="url_count_input")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Update", key="update_count", use_container_width=True):
            st.session_state.url_count = url_count
            st.rerun()
    
    # Generate URL input fields
    custom_urls = []
    for i in range(st.session_state.url_count):
        url = st.text_input(
            f"URL {i+1}", 
            key=f"custom_url_{i}", 
            placeholder="https://example.com/article",
            help=f"Enter a valid URL to process and analyze"
        )
        if url.strip():
            custom_urls.append(url.strip())
    
    # URL validation and preview
    if custom_urls:
        st.markdown("**📋 URLs ready for processing:**")
        for i, url in enumerate(custom_urls, 1):
            domain = url.split('/')[2] if len(url.split('/')) > 2 else url
            st.markdown(f"✅ **{i}.** {domain}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Processing Section
  
    st.markdown("#### ⚡ AI Processing")
    
    if st.button("🚀 Process & Analyze", type="primary", use_container_width=True):
        if not custom_urls:
            st.error("Please add at least one valid URL!")
        else:
            start_time = time.time()
            
            with st.spinner("🧠 AI is analyzing your content..."):
                progress_bar = st.progress(0)
                status_container = st.empty()
                
                try:
                    status_container.info("🔄 Initializing AI processing pipeline...")
                    progress_bar.progress(0.2)
                    time.sleep(0.5)
                    
                    status_container.info("📥 Extracting content from URLs...")
                    progress_bar.progress(0.4)
                    
                    status_list = list(process_urls(custom_urls))
                    
                    status_container.info("🧠 Creating intelligent embeddings...")
                    progress_bar.progress(0.8)
                    time.sleep(0.5)
                    
                    end_time = time.time()
                    processing_time = round(end_time - start_time, 2)
                    
                    progress_bar.progress(1.0)
                    status_container.success(f"✅ AI processing completed in {processing_time}s")
                    
                    st.session_state.processed_urls = custom_urls
                    st.session_state.last_update = datetime.now()
                    st.success(f"🎉 Successfully processed {len(custom_urls)} documents in {processing_time}s!")
                    
                except Exception as e:
                    end_time = time.time()
                    processing_time = round(end_time - start_time, 2)
                    st.error(f"❌ Processing failed after {processing_time}s: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Enhanced System Status
    st.markdown("#### 📈 System Status")
    
    if st.session_state.processed_urls:
        st.success(f"✅ {len(st.session_state.processed_urls)} documents ready")
        if st.session_state.last_update:
            st.info(f"🕒 Last update: {st.session_state.last_update.strftime('%H:%M:%S')}")
        st.metric("Processing Status", "Active", delta="Ready for queries")
    else:
        st.warning("⚠️ No documents processed yet")
        st.info("👆 Add URLs above and click 'Process & Analyze'")
    
    # Clear data option
    if st.button("🗑️ Clear All Data", use_container_width=True, help="Reset all processed data and queries"):
        st.session_state.processed_urls = []
        st.session_state.last_update = None
        st.session_state.query_history = []
        st.success("🧹 All data cleared successfully!")
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main content area with better proportions
col1, col2 = st.columns([2.5, 1.5])

with col1:
    # Enhanced Query Interface
    st.markdown("### 💬 Ask Your AI Assistant")
    
    # Custom query input with better styling
    query = st.text_area(
        "What would you like to know about your processed content?",
        height=120,
        placeholder="Ask anything about your documents: summarize key points, find specific information, compare content, or get insights...",
        help="Your AI assistant can analyze, summarize, and answer questions about the processed content"
    )
    
    # Query execution with enhanced feedback
    query_col1, query_col2 = st.columns([3, 1])
    with query_col1:
        ask_button = st.button("🔍 Ask AI Assistant", type="primary", disabled=not query, use_container_width=True)
    with query_col2:
        if st.session_state.query_history:
            st.button("📜 View History", use_container_width=True)
    
    if ask_button:
        if not st.session_state.processed_urls:
            st.error("⚠️ Please process some URLs first using the sidebar!")
        else:
            with st.spinner("🤖 AI is analyzing and generating your answer..."):
                try:
                    answer, sources = generate_answer(query)
                    
                    # Add to query history
                    st.session_state.query_history.append({
                        'question': query,
                        'answer': answer,
                        'sources': sources,
                        'timestamp': datetime.now()
                    })
                    
                    # Display answer with enhanced styling
                    st.markdown("### 🎯 AI Response")
                    st.markdown(f'<div class="feature-card"><strong>Answer:</strong><br>{answer}</div>', unsafe_allow_html=True)
                    
                    # Display sources with better formatting
                    if sources:
                        st.markdown("### 📚 Source References")
                        source_list = sources.split("\n")
                        for i, source in enumerate(source_list, 1):
                            if source.strip():
                                st.markdown(f"**{i}.** {source.strip()}")
                    
                except Exception as e:
                    st.error(f"❌ Error generating answer: {str(e)}")

with col2:
    # Enhanced Analytics Dashboard
    st.markdown("### 📊 Analytics Dashboard")
    
    # Enhanced Metrics
    if st.session_state.query_history:
        total_queries = len(st.session_state.query_history)
        total_docs = len(st.session_state.processed_urls)
        
        # Create metric cards
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; color:#667eea;">{total_queries}</h3>
            <p style="margin:0; color:#64748b;">Total Queries</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0; color:#764ba2;">{total_docs}</h3>
            <p style="margin:0; color:#64748b;">Documents Processed</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced Query History
    st.markdown("### 📝 Recent Interactions")
    
    if st.session_state.query_history:
        # Show last 3 queries with better formatting
        for i, query_data in enumerate(reversed(st.session_state.query_history[-3:])):
            with st.expander(f"💬 {query_data['question'][:40]}..."):
                st.markdown(f"**⏰ Time:** {query_data['timestamp'].strftime('%H:%M:%S')}")
                st.markdown(f"**🤖 Response:** {query_data['answer'][:150]}...")
                if st.button(f"🔄 Ask Again", key=f"rerun_{i}", use_container_width=True):
                    st.session_state.current_query = query_data['question']
                    st.rerun()
    else:
        st.info("💡 No interactions yet. Process some URLs and ask your first question!")
    
    # Enhanced Quick Stats
    st.markdown("### 📈 System Overview")
    if st.session_state.processed_urls:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.95); padding: 1.5rem; border-radius: 16px; margin: 1rem 0;">
            <h4 style="margin-top:0; color:#334155;">📊 Current Session</h4>
            <p><strong>📄 Documents:</strong> {len(st.session_state.processed_urls)}</p>
            <p><strong>🕒 Last Update:</strong> {st.session_state.last_update.strftime('%H:%M') if st.session_state.last_update else 'Never'}</p>
            <p><strong>💬 Total Queries:</strong> {len(st.session_state.query_history)}</p>
            <p><strong>🎯 Status:</strong> <span style="color: #059669;">Ready</span></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show processed URLs in an expandable section
        with st.expander("📋 View All Processed Documents"):
            for i, url in enumerate(st.session_state.processed_urls, 1):
                domain = url.split('/')[2] if len(url.split('/')) > 2 else url
                st.markdown(f"**{i}.** {domain}")
                st.caption(url)

# Replace the footer section (around lines 704-765) with this simplified version
st.markdown("""
<div class="modern-footer">
    <div class="footer-content">
        <div class="footer-grid">
            <div class="footer-brand-section">
                <div class="footer-brand">🤖 Docubot</div>
                <div class="footer-description">
                    Transform any web content into intelligent, searchable knowledge with AI-powered analysis.
                </div>
                <div class="footer-features">
                    <span class="feature-tag">⚡ AI-Powered</span>
                    <span class="feature-tag">🔒 Secure</span>
                    <span class="feature-tag">🚀 Fast</span>
                </div>
            </div>
        </div>
        <div class="footer-bottom">
            <div class="footer-copyright">
                © 2025 Docubot | Built with ❤️ using Streamlit & Advanced AI
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
