from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_aws import ChatBedrock
from langchain_postgres import PGVector
from langchain_aws import BedrockEmbeddings
from langchain_core.runnables import RunnablePassthrough


embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0", region_name="eu-north-1")
vectorstore = PGVector(embeddings=embeddings, connection="postgresql://...", collection_name="my_docs") #Postgres connection
retriever = vectorstore.as_retriever()


prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer based only on context below.\n\nContext: {context}"),
    ("user", "{question}")
])

llm = ChatBedrock(
    model_id="eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name="eu-north-1"
)

parser = StrOutputParser()

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | parser
)

result = rag_chain.invoke("What is LangGraph?")
print(result)