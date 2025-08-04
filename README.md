
### Technology Stack

- **Frontend**: Streamlit with custom CSS styling
- **Backend**: Python with LangChain framework
- **LLM**: Groq's LLaMA 3.3 70B Versatile model
- **Embeddings**: SentenceTransformers (sentence-t5-large)
- **Vector Database**: Chroma with persistent storage
- **Web Scraping**: Unstructured + Selenium fallback

## 🚀 Installation

### Prerequisites

- Python 3.8+
- pip package manager
- Groq API key

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Real_Estate
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your Groq API key
   echo "GROQ_API_KEY=your_groq_api_key_here" > .env
   ```

5. **Run the application**
   ```bash
   streamlit run main.py
   ```

6. **Access the application**
   Open your browser and navigate to `http://localhost:8501`

## 💻 Usage

### Processing URLs

1. **Add URLs**: Enter one or more URLs in the sidebar input fields
2. **Process**: Click "Process URLs" to extract and analyze content
3. **Monitor**: Watch real-time processing status and completion times

### Querying Documents

1. **Ask Questions**: Use the main query interface to ask questions
2. **Get Answers**: Receive AI-generated responses with source citations
3. **View Sources**: Expand source sections to see original content

### Analytics Dashboard

- **Processing Stats**: View document processing metrics
- **Query History**: Track all previous questions and answers
- **Session Overview**: Monitor current session statistics

## ⚙️ Configuration

### Environment Variables

```bash
# Required
GROQ_API_KEY=your_groq_api_key

# Optional
CHUNK_SIZE=400                    # Text chunk size for processing
EMBEDDING_MODEL=sentence-transformers/sentence-t5-large
VECTORSTORE_DIR=./resources/vectorstore
COLLECTION_NAME=real_estate
```

### Model Configuration

```python
# LLM Settings (in rag.py)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.1,              # Low temperature for consistent answers
    max_tokens=1500,              # Increased for detailed responses
    top_p=0.9,
    frequency_penalty=0.1,
    presence_penalty=0.1
)
```

## 📚 API Reference

### Core Functions

#### `process_urls(urls: List[str]) -> Generator`
Processes a list of URLs and yields status updates.

**Parameters:**
- `urls`: List of URL strings to process

**Returns:**
- Generator yielding processing status dictionaries

#### `generate_answer(query: str) -> Tuple[str, List[str]]`
Generates an AI answer for the given query.

**Parameters:**
- `query`: Question string

**Returns:**
- Tuple of (answer, sources)

### Streamlit Components

- **URL Input**: Multi-field URL entry system
- **Processing Display**: Real-time status updates
- **Query Interface**: Main Q&A interaction
- **Analytics Dashboard**: Session statistics and history

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
