import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

api_key = os.getenv("GEMINI_API_KEY")
model = "gemini-3-flash-preview"
prompt = "Explain quantum computing in simple terms."

llm = ChatGoogleGenerativeAI(model=model, google_api_key=api_key)
response = llm.invoke([HumanMessage(content=prompt)])

print(f"Model: {model}")
print(response.content)
