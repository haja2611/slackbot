#query_rag1.py
import os
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language

# Supported code languages
SUPPORTED_LANGUAGES = [
    'cpp', 'go', 'java', 'kotlin', 'js', 'typescript', 'php', 'proto', 'python',
    'rst', 'ruby', 'rust', 'scala', 'swift', 'markdown', 'latex', 'html',
    'sol', 'csharp', 'cobol'
]


# Code splitters for each supported language
CODE_SPLITTERS = {
    'cpp': RecursiveCharacterTextSplitter.from_language(Language.CPP, chunk_size=1000, chunk_overlap=0),
    'go': RecursiveCharacterTextSplitter.from_language(Language.GO, chunk_size=1000, chunk_overlap=0),
    'java': RecursiveCharacterTextSplitter.from_language(Language.JAVA, chunk_size=1000, chunk_overlap=0),
    'js': RecursiveCharacterTextSplitter.from_language(Language.JS, chunk_size=1000, chunk_overlap=0),
    'python': RecursiveCharacterTextSplitter.from_language(Language.PYTHON, chunk_size=1000, chunk_overlap=0),
    'rst': RecursiveCharacterTextSplitter.from_language(Language.RST, chunk_size=1000, chunk_overlap=0),
    'ruby': RecursiveCharacterTextSplitter.from_language(Language.RUBY, chunk_size=1000, chunk_overlap=0),
    'rust': RecursiveCharacterTextSplitter.from_language(Language.RUST, chunk_size=1000, chunk_overlap=0),
    'scala': RecursiveCharacterTextSplitter.from_language(Language.SCALA, chunk_size=1000, chunk_overlap=0),
    'swift': RecursiveCharacterTextSplitter.from_language(Language.SWIFT, chunk_size=1000, chunk_overlap=0),
    'markdown': RecursiveCharacterTextSplitter.from_language(Language.MARKDOWN, chunk_size=1000, chunk_overlap=0),
    'latex': RecursiveCharacterTextSplitter.from_language(Language.LATEX, chunk_size=1000, chunk_overlap=0),
    'html': RecursiveCharacterTextSplitter.from_language(Language.HTML, chunk_size=1000, chunk_overlap=0),
    'sol': RecursiveCharacterTextSplitter.from_language(Language.SOL, chunk_size=1000, chunk_overlap=0),
}

class Document:
    def __init__(self, file_path):
        self.file_path = file_path
        self.content = self.load_content()
        self.page_content = self.content
        self.metadata = {} 

    def load_content(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            print(f"File '{self.file_path}' not found.")
            return None

    def get_chunks(self, chunk_size):
        if self.content:
            for i in range(0, len(self.content), chunk_size):
                yield self.content[i:i+chunk_size]


def main():

    directory_path = "./git_data"
    all_chunks = [] 

    for root, dirs, _ in os.walk(directory_path):
        for dir_name in dirs:
            repo_path = os.path.join(root, dir_name)
            create_chunks(repo_path, all_chunks)
    retriever = store_and_ask_questions(all_chunks)
    return retriever

def create_chunks(repo_path, all_chunks):
    """
    Create chunks for code files within a repository.

    Args:
        repo_path: Path to the repository directory.
    """
    files = os.listdir(repo_path)

    
    for file in files:
        file_path = os.path.join(repo_path, file)
        if os.path.isfile(file_path):
            # Get the file extension
            _, extension = os.path.splitext(file_path)
            print("File:", file, "Extension:", extension) 
            
            # Detect the language of the file based on its extension
            language = detect_language(extension)
            if language:
                code_splitter = get_code_splitter(language)
                document = Document(file_path) 
                chunks = code_splitter.split_documents([document])
                if chunks:
                    all_chunks.extend(chunks) 
            
            else:
                print(f"Unsupported file: {file_path}")
        else:
            print(f"Ignoring non-file item: {file_path}")

def detect_language(extension):
    """
    Detect the programming language based on the file extension.

    Args:
        extension (str): File extension.

    Returns:
        str: Detected language or None if not found.
    """
   
    LANGUAGE_FILE_EXTENSIONS = {
        'cpp': ['.cpp', '.hpp', '.h'],
        'go': ['.go'],
        'java': ['.java'],
        'kotlin': ['.kt'],
        'js': ['.js'],
        'typescript': ['.ts'],
        'php': ['.php'],
        'proto': ['.proto'],
        'python': ['.py'],
        'rst': ['.rst'],
        'ruby': ['.rb'],
        'rust': ['.rs'],
        'scala': ['.scala'],
        'swift': ['.swift'],
        'markdown': ['.md'],
        'latex': ['.tex'],
        'html': ['.html'],
        'sol': ['.sol'],
        'csharp': ['.cs'],
        'cobol': ['.cobol'],
        'markdown': ['.md'],
    }

    for language, extensions in LANGUAGE_FILE_EXTENSIONS.items():
        if extension in extensions:
            return language

    return None


def get_code_splitter(language):
    """
    Get the appropriate code splitter based on the language.

    Args:
        language (str): Language of the document.

    Returns:
        RecursiveCharacterTextSplitter: Code splitter instance.
    """
    if language in SUPPORTED_LANGUAGES:
        return CODE_SPLITTERS.get(language, RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0))
    else:
        return RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

def store_and_ask_questions(all_chunks):
    """
    Store embeddings for all chunks and prompt the user to ask questions.

    Args:
        all_chunks: List containing all document chunks.
    """
    embeddings = OllamaEmbeddings(model="phi")
    vectorstore = Chroma.from_documents(documents=all_chunks, embedding=embeddings, persist_directory="./chroma_db")
    print("Embeddings stored successfully.")
    # Create the retriever
    retriever = vectorstore.as_retriever()
    return retriever
  
if __name__ == '__main__':
    main()
