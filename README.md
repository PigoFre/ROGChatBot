# ROGChatBot
The aim of the project is to develop an adaptive chatbot tailored for answering questions about data studies based on a set of academic journal articles and conference papers.
Description: The system is an adaptive RAG chatbot for the Data Studies Bibliography. A command-line ingestion pipeline processes approved PDF articles into chunked, embedded, metadata-rich records stored in a local vector database. A web chat interface retrieves relevant passages and uses either a local open model or a commercial API model to generate grounded responses with citations. User feedback is logged and used to iteratively improve retrieval, prompting, and answer quality.


Python Libraries:


astapi or flask


OPENA AI, for global calls!


pymupdf or pdfplumber for PDF extraction

chromadb

ollama or direct HTTP calls to Ollama API

optionally langchain if you want faster setup

