from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.prompts.system_prompts import codeAgentSystemPrompt

from dotenv import load_dotenv
load_dotenv()

import os

os.environ['GROQ_API_KEY']=os.getenv("groq_api_key")

codeAgent = ChatPromptTemplate([('ai',f"{codeAgentSystemPrompt}"),
                                ("human","{user_input}")]) | ChatGroq(model="openai/gpt-oss-20b",temperature=0) 

def codeAgentGen(user_input:str):
    response = codeAgent.invoke({"user_input":user_input}).content
    print("code generated :- \n",response)
    
    return response