import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import copy
import logging
from pydantic.v1 import utils
from uuid import uuid4
from dotenv import load_dotenv
from pathlib import Path
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_community.embeddings import SentenceTransformerEmbeddings
from transformers import AutoTokenizer
from unstructured.cleaners.core import clean_extra_whitespace, remove_punctuation

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Patch smart_deepcopy to handle classmethod
original_smart_deepcopy = utils.smart_deepcopy

def patched_smart_deepcopy(obj):
    if isinstance(obj, classmethod):
        return obj
    return original_smart_deepcopy(obj)

utils.smart_deepcopy = patched_smart_deepcopy

load_dotenv()

# Constants
CHUNK_SIZE = 400  # Increased from 200 for better context
EMBEDDING_MODEL = "sentence-transformers/sentence-t5-large"
VECTORSTORE_DIR = Path(__file__).parent / "resources/vectorstore"
COLLECTION_NAME = "real_estate"

llm = None
vector_store = None

def initialize_components():
    global llm, vector_store
    logging.info("Initializing components...")
    
    if llm is None:
        try:
            # Optimized LLM configuration for better, more reliable answers
            llm = ChatGroq(
                model="llama-3.3-70b-versatile", 
                temperature=0.1,  # Lower temperature for more consistent, factual responses
                max_tokens=1500,  # Increased token limit for more detailed answers
                top_p=0.9,       # Focus on most likely tokens
                frequency_penalty=0.1,  # Reduce repetition
                presence_penalty=0.1    # Encourage diverse vocabulary
            )
            logging.info("LLM initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize LLM: {e}")
            raise

    if vector_store is None:
        try:
            ef = SentenceTransformerEmbeddings(
                model_name=EMBEDDING_MODEL
            )
            vector_store = Chroma(
                collection_name=COLLECTION_NAME,
                embedding_function=ef,
                persist_directory=str(VECTORSTORE_DIR)
            )
            logging.info("Vector store initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize vector store: {e}")
            raise

def process_urls(urls):
    """
    This function scrapes data from a url and stores it in a vector db
    :param urls: input urls
    :return:
    """
    yield "Initializing Components"
    try:
        initialize_components()
    except Exception as e:
        logging.error(f"Error initializing components: {e}")
        yield f"Error initializing components: {e}"
        return

    yield "Resetting vector store...✅"
    try:
        vector_store.reset_collection()
        logging.info("Vector store reset successfully")
    except Exception as e:
        logging.error(f"Error resetting vector store: {e}")
        yield f"Error resetting vector store: {e}"
        return

    yield "Loading data...✅"
    try:
        # Clean URLs by removing fragments and query parameters that might cause issues
        cleaned_urls = []
        for url in urls:
            # Remove fragments (#) and clean the URL
            if '#' in url:
                url = url.split('#')[0]
            cleaned_urls.append(url)
            logging.info(f"Cleaned URL: {url}")
        
        # Try multiple user agents and methods
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        data = []
        successful_loads = 0
        
        # Method 1: Try UnstructuredURLLoader with different configurations
        for i, user_agent in enumerate(user_agents):
            if successful_loads >= len(cleaned_urls):
                break
                
            try:
                logging.info(f"Trying UnstructuredURLLoader with user agent {i+1}")
                loader = UnstructuredURLLoader(
                    urls=cleaned_urls,
                    headers={
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Cache-Control": "max-age=0"
                    },
                    ssl_verify=False,
                    requests_kwargs={
                        "timeout": 30,
                        "allow_redirects": True,
                        "stream": False
                    }
                )
                temp_data = loader.load()
                
                for doc in temp_data:
                    if len(doc.page_content.strip()) > 0:
                        data.append(doc)
                        successful_loads += 1
                        logging.info(f"UnstructuredURLLoader success: {len(doc.page_content)} chars from {doc.metadata.get('source', 'unknown')}")
                
                if successful_loads > 0:
                    break
                    
            except Exception as e:
                logging.warning(f"UnstructuredURLLoader attempt {i+1} failed: {e}")
                continue
        
        # Method 2: Advanced requests with session and multiple strategies
        if successful_loads == 0:
            yield "Trying advanced content extraction methods..."
            import requests
            from bs4 import BeautifulSoup
            import time
            
            session = requests.Session()
            
            for url in cleaned_urls:
                success = False
                
                # Try different approaches for each URL
                strategies = [
                    # Strategy 1: Standard request with session
                    {
                        "headers": {
                            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "Accept-Language": "en-US,en;q=0.5",
                            "Accept-Encoding": "gzip, deflate",
                            "Connection": "keep-alive",
                            "Upgrade-Insecure-Requests": "1"
                        },
                        "verify": False,
                        "timeout": 30
                    },
                    # Strategy 2: Mobile user agent
                    {
                        "headers": {
                            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                        },
                        "verify": False,
                        "timeout": 30
                    },
                    # Strategy 3: Minimal headers
                    {
                        "headers": {
                            "User-Agent": "curl/7.68.0"
                        },
                        "verify": False,
                        "timeout": 30
                    }
                ]
                
                for i, strategy in enumerate(strategies):
                    try:
                        logging.info(f"Trying strategy {i+1} for {url}")
                        
                        # Add small delay between requests
                        if i > 0:
                            time.sleep(2)
                        
                        response = session.get(url, **strategy)
                        
                        # Check for different success conditions
                        if response.status_code == 200:
                            # Parse with BeautifulSoup
                            soup = BeautifulSoup(response.content, 'html.parser')
                            
                            # Remove unwanted elements
                            for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
                                element.decompose()
                            
                            # Extract text content
                            text = soup.get_text(separator=' ', strip=True)
                            
                            # Clean up extra whitespace
                            text = ' '.join(text.split())
                            
                            if len(text.strip()) > 100:
                                from langchain.schema import Document
                                doc = Document(page_content=text.strip(), metadata={"source": url})
                                data.append(doc)
                                successful_loads += 1
                                success = True
                                logging.info(f"Strategy {i+1} success: extracted {len(text)} chars from {url}")
                                break
                            else:
                                logging.warning(f"Strategy {i+1}: Content too short ({len(text)} chars)")
                        else:
                            logging.warning(f"Strategy {i+1}: HTTP {response.status_code} for {url}")
                            
                    except Exception as e:
                        logging.warning(f"Strategy {i+1} failed for {url}: {e}")
                        continue
                
                if not success:
                    logging.error(f"All strategies failed for {url}")
        
        # Method 3: Try with selenium as last resort (if available)
        if successful_loads == 0:
            try:
                yield "Trying browser automation as last resort..."
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                driver = webdriver.Chrome(options=chrome_options)
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                for url in cleaned_urls:
                    try:
                        driver.get(url)
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        
                        # Get page text
                        text = driver.find_element(By.TAG_NAME, "body").text
                        
                        if len(text.strip()) > 100:
                            from langchain.schema import Document
                            doc = Document(page_content=text.strip(), metadata={"source": url})
                            data.append(doc)
                            successful_loads += 1
                            logging.info(f"Selenium success: extracted {len(text)} chars from {url}")
                        
                    except Exception as e:
                        logging.warning(f"Selenium failed for {url}: {e}")
                
                driver.quit()
                
            except ImportError:
                logging.info("Selenium not available, skipping browser automation")
            except Exception as e:
                logging.warning(f"Selenium method failed: {e}")
        
        # Validate results
        if not data or successful_loads == 0:
            error_msg = f"Unable to extract content from any of the {len(urls)} URLs. This could be due to:\n"
            error_msg += "1. Websites blocking automated access (403/404 errors)\n"
            error_msg += "2. Content loaded dynamically with JavaScript\n"
            error_msg += "3. URLs requiring authentication or special access\n"
            error_msg += "4. Network connectivity issues\n\n"
            error_msg += "Please try:\n"
            error_msg += "- Using different URLs that are more accessible\n"
            error_msg += "- Checking if the URLs work in a regular browser\n"
            error_msg += "- Using URLs from sites that allow web scraping"
            
            logging.error(error_msg)
            yield f"Error: {error_msg}"
            return
        
        # Clean and validate documents
        valid_docs = []
        for i, doc in enumerate(data):
            logging.info(f"Document {i} original length: {len(doc.page_content)} characters")
            
            # Clean whitespace but preserve content
            doc.page_content = clean_extra_whitespace(doc.page_content)
            
            # Lenient validation
            if len(doc.page_content.strip()) > 10:
                cleaned_content = doc.page_content.strip()
                doc.page_content = cleaned_content
                valid_docs.append(doc)
                logging.info(f"Document {i} cleaned length: {len(doc.page_content)} characters")
            else:
                logging.warning(f"Document {i} too short after cleaning ({len(doc.page_content)} chars), skipping")
        
        if not valid_docs:
            logging.error("No valid documents found after cleaning")
            yield "Error: Content was extracted but became invalid after cleaning"
            return
            
        data = valid_docs
        logging.info(f"Successfully processed {len(data)} documents")
        
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        yield f"Error loading data: {e}"
        return

    yield "Splitting text into chunks...✅"
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ".", "!", "?", ";", " "],  # More granular separators
            chunk_size=CHUNK_SIZE,
            chunk_overlap=100,  # Increased overlap for better continuity
            length_function=len,
            is_separator_regex=False
        )
        docs = text_splitter.split_documents(data)
        logging.info(f"Split into {len(docs)} chunks")
        
        # Filter out empty chunks with more lenient criteria
        docs = [doc for doc in docs if len(doc.page_content.strip()) > 10]
        logging.info(f"After filtering empty chunks: {len(docs)} chunks remain")
        
        if not docs:
            logging.error("No chunks remain after splitting")
            yield "Error: Content could not be properly split into chunks"
            return
        
    except Exception as e:
        logging.error(f"Error splitting text: {e}")
        yield f"Error splitting text: {e}"
        return

    # Filter chunks by token length
    yield "Filtering chunks by token length...✅"
    try:
        tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
        max_tokens = 256
        filtered_docs = []
        
        for i, doc in enumerate(docs):
            # Skip empty documents
            if not doc.page_content.strip():
                logging.warning(f"Skipping empty chunk {i}")
                continue
                
            tokens = tokenizer.encode(doc.page_content, add_special_tokens=True)
            logging.info(f"Chunk {i} token length: {len(tokens)}")
            
            if len(tokens) <= max_tokens and len(tokens) > 2:  # Reduced from 5 to 2
                filtered_docs.append(doc)
            elif len(tokens) > max_tokens:
                truncated_text = tokenizer.decode(tokens[:max_tokens], skip_special_tokens=True)
                if len(truncated_text.strip()) > 3:  # Reduced from 10 to 3
                    doc.page_content = truncated_text.strip()
                    filtered_docs.append(doc)
                    logging.info(f"Truncated chunk {i} to {len(tokenizer.encode(truncated_text, add_special_tokens=True))} tokens")
                else:
                    logging.warning(f"Truncated chunk {i} too short, skipping")
            else:
                logging.warning(f"Chunk {i} has too few tokens ({len(tokens)}), skipping")
        
        if not filtered_docs:
            logging.error("No valid chunks found after filtering")
            yield "Error: No valid content chunks found after token filtering"
            return
            
        logging.info(f"Final filtered documents: {len(filtered_docs)}")
        
    except Exception as e:
        logging.error(f"Error filtering chunks: {e}")
        yield f"Error filtering chunks: {e}"
        return

    yield "Add chunks to vector database...✅"
    try:
        if not filtered_docs:
            raise ValueError("No documents to add to vector store")
            
        # Double-check all documents have content with lenient criteria
        valid_filtered_docs = []
        for doc in filtered_docs:
            if doc.page_content and len(doc.page_content.strip()) > 2:  # Reduced from 5 to 2
                valid_filtered_docs.append(doc)
            else:
                logging.warning(f"Skipping document with empty/minimal content: '{doc.page_content[:50]}'")
        
        if not valid_filtered_docs:
            raise ValueError("All documents are empty after final validation")
        
        uuids = [str(uuid4()) for _ in range(len(valid_filtered_docs))]
        vector_store.add_documents(valid_filtered_docs, ids=uuids)
        logging.info(f"Added {len(valid_filtered_docs)} documents to vector store")
        
    except Exception as e:
        logging.error(f"Error adding documents to vector store: {e}")
        yield f"Error adding documents to vector store: {e}"
        return

    yield "Done adding docs to vector database...✅"

def generate_answer(query):
    if not vector_store:
        logging.error("Vector database is not initialized")
        raise RuntimeError("Vector database is not initialized")

    try:
        # Enhanced retrieval configuration
        retriever = vector_store.as_retriever(
            search_type="mmr",  # Maximum Marginal Relevance for diverse results
            search_kwargs={
                "k": 6,           # Increased from 3 to get more context
                "fetch_k": 12,   # Fetch more candidates before MMR filtering
                "lambda_mult": 0.7  # Balance between relevance and diversity
            }
        )
        
        # Test retrieval to ensure we have relevant documents
        retrieved_docs = retriever.get_relevant_documents(query)
        if not retrieved_docs:
            logging.warning("No relevant documents found for the query")
            return "I couldn't find any relevant information in the knowledge base to answer your question. Please try rephrasing your question or ensure the relevant content has been loaded.", ""
        
        logging.info(f"Retrieved {len(retrieved_docs)} documents for query: {query}")
        for i, doc in enumerate(retrieved_docs):
            logging.info(f"Doc {i+1}: {len(doc.page_content)} chars from {doc.metadata.get('source', 'unknown')}")
        
        # Create custom prompt for better responses
        from langchain.prompts import PromptTemplate
        from langchain.chains import RetrievalQA
        
        # Custom prompt template for more reliable answers
        custom_prompt = PromptTemplate(
            template="""You are an intelligent assistant that provides accurate, detailed answers based on the given context. 

Context information:
{context}

Question: {question}

Instructions:
1. Provide a comprehensive answer based ONLY on the information in the context above
2. If the context contains relevant information, provide a detailed, well-structured response
3. Include specific details, numbers, dates, and facts when available
4. If the context doesn't contain enough information to fully answer the question, say "Based on the available information..." and provide what you can
5. NEVER say "I don't know" - always try to extract and present any relevant information from the context
6. Organize your response clearly with proper formatting
7. Be specific and cite relevant details from the source material

Answer:""",
            input_variables=["context", "question"]
        )
        
        # Use RetrievalQA with custom prompt instead of RetrievalQAWithSourcesChain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={
                "prompt": custom_prompt,
                "verbose": True
            },
            return_source_documents=True
        )
        
        # Generate answer
        result = qa_chain.invoke({"query": query})
        answer = result['result']
        source_docs = result['source_documents']
        
        # Extract sources
        sources = []
        for doc in source_docs:
            source = doc.metadata.get('source', 'Unknown')
            if source not in sources:
                sources.append(source)
        
        sources_str = ", ".join(sources) if sources else "No sources available"
        
        # Post-process answer to ensure quality
        if not answer or answer.strip().lower() in ["i don't know", "i don't know.", "unknown", "not available"]:
            # Fallback: try to extract any useful information from retrieved docs
            context_summary = ""
            for doc in retrieved_docs[:3]:  # Use top 3 docs
                context_summary += doc.page_content[:200] + "... "
            
            if context_summary.strip():
                answer = f"Based on the available information: {context_summary.strip()}"
            else:
                answer = "I couldn't find specific information to answer your question in the current knowledge base."
        
        logging.info(f"Generated answer for query: {query}")
        logging.info(f"Answer length: {len(answer)} characters")
        logging.info(f"Sources: {sources_str}")
        
        return answer, sources_str
        
    except Exception as e:
        logging.error(f"Error generating answer: {e}")
        # Provide a more helpful error message
        return f"I encountered an error while processing your question: {str(e)}. Please try rephrasing your question or contact support if the issue persists.", ""

if __name__ == "__main__":
    urls = [
        "https://www.bankrate.com/mortgages/30-year-mortgage-rates/",
        "https://www.freddiemac.com/pmms"
    ]

    try:
        for status in process_urls(urls):
            print(status)
    except Exception as e:
        logging.error(f"Error processing URLs: {e}")
        print(f"Error processing URLs: {e}")

    # Ensure vector store is initialized before generating answer
    if not vector_store:
        try:
            initialize_components()
        except Exception as e:
            logging.error(f"Error initializing components before query: {e}")
            print(f"Error initializing components before query: {e}")
            exit(1)

    try:
        answer, sources = generate_answer("Tell me what was the 30 year fixed mortgage rate along with the date?")
        print(f"Answer: {answer}")
        print(f"Sources: {sources}")
    except Exception as e:
        logging.error(f"Error generating answer: {e}")
        print(f"Error generating answer: {e}")