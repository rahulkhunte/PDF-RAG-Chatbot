import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
import os
import tempfile

# Initialize session state
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Page config
st.set_page_config(
    page_title="PDF Knowledge Base Chatbot", 
    page_icon="🧠", 
    layout="wide"
)

# Main title with branding
st.title("🧠 PDF Knowledge Base Chatbot")
st.markdown("**Powered by Llama 3.1 | Built on NVIDIA L40 Enterprise GPU**")
st.markdown("Upload PDFs and ask questions - AI answers with source citations")

# Sidebar for PDF upload
with st.sidebar:
    st.header("📤 Upload Documents")
    st.markdown("🚀 **Built by Rahul | Enterprise AI Solutions**")
    
    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload product manuals, reports, documentation, etc."
    )
    
    process_button = st.button("⚡ Process PDFs", type="primary")
    
    if process_button and uploaded_files:
        with st.spinner("Processing PDFs on L40 GPU..."):
            # Save uploaded files temporarily
            docs = []
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_path = tmp_file.name
                
                # Load PDF
                loader = PyPDFLoader(tmp_path)
                docs.extend(loader.load())
                os.unlink(tmp_path)
            
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(docs)
            
            # Create embeddings
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            # Create vector store
            st.session_state.vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=embeddings,
                persist_directory="/tmp/chroma_db"
            )
            
            st.success(f"✅ Processed {len(uploaded_files)} PDFs ({len(splits)} chunks)")
            st.balloons()
            st.session_state.chat_history = []

# Main chat interface
if st.session_state.vectorstore:
    st.markdown("### 💬 Ask Questions")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message:
                with st.expander("📄 View Sources"):
                    st.markdown(message["sources"])
    
    # Chat input
    if question := st.chat_input("Ask a question about your documents..."):
        # Add user message to chat
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("🧠 Thinking on L40 GPU..."):
                # Retrieve relevant documents
                docs = st.session_state.vectorstore.similarity_search(question, k=3)
                
                # Build context from documents
                context = "\n\n".join([doc.page_content for doc in docs])
                
                # Create prompt
                prompt = f"""Use the following pieces of context to answer the question at the end. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Always cite the source page number when possible.

Context: {context}

Question: {question}

Answer:"""
                
                # Get LLM response
                llm = Ollama(model="llama3.1:8b", temperature=0.1)
                answer = llm.invoke(prompt)
                
                # Display answer
                st.markdown(answer)
                
                # Format sources
                source_text = "\n\n".join([
                    f"**Source {i+1}:** {doc.page_content[:200]}... (Page {doc.metadata.get('page', 'N/A')})"
                    for i, doc in enumerate(docs)
                ])
                
                # Display sources
                with st.expander("📄 View Sources"):
                    st.markdown(source_text)
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": source_text
                })
else:
    st.info("👈 Upload PDFs in the sidebar to get started")
    
    # Demo instructions
    st.markdown("""
    ### 🎯 How it works:
    1. **Upload PDFs** in the sidebar (product manuals, reports, documentation, etc.)
    2. **Click "⚡ Process PDFs"** to index the documents
    3. **Ask questions** and get accurate answers with source citations
    
    ### 💡 Try asking:
    - *"Summarize this document in 3 bullet points"*
    - *"What are the main features?"*
    - *"What is the refund policy?"*
    - *"What are the safety guidelines?"*
    
    ### ⚡ Why This Bot:
    - **No API Costs** - 100% local Llama 3.1 (you own the data)
    - **Fast Processing** - Enterprise NVIDIA L40 GPU
    - **Source Citations** - Always shows where answers come from
    - **Privacy First** - Your data never leaves your infrastructure
    """)

# Footer
st.markdown("---")
st.markdown("🧠 **Built with Llama 3.1 on NVIDIA L40** | 🚀 Deployable in 24 hours | 📦 No OpenAI API needed")
