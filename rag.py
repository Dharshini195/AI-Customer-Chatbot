from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader,Docx2txtLoader
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
filepath = os.path.join(current_dir,"company_policies.docx")
chroma_directory = os.path.join(current_dir,"db", "chroma_db")


def retreiever_rag(query):
    try:
        if not os.path.exists(chroma_directory):

            loader = Docx2txtLoader(filepath)
            documents = loader.load()

            text_splitter = CharacterTextSplitter(chunk_size=200,chunk_overlap=20)
            chunks = text_splitter.split_documents(documents)

            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

            db = Chroma.from_documents(chunks,embeddings,persist_directory=chroma_directory)


        else:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")   
            db = Chroma(persist_directory=chroma_directory,embedding_function=embeddings)

        retreiever = db.as_retriever(search_kwargs={"k":3 })
        
        relevant_docs = retreiever.invoke(query)
        
        return relevant_docs
    except:
        import traceback
        print(f"Error : {traceback.format_exc()}")
    
