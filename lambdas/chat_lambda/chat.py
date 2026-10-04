import os

from openai import OpenAI
from fastapi import FastAPIRouter
from common_helper.models.chat import ChatRequest

client = OpenAI(api_key=os.getenv('GROQ_API_KEY'), base_url=os.getenv('BASE_URL_OPEN_AI'))


router = FastAPIRouter(prefix="/chat", tags=["chat"])

@router.post('/ask')
def chat_api(req: ChatRequest):
    message = [{"role": "system", "content": "You are a helpful assistant."}]
    message.extend(req.history)
    message.append({"role": "user", "content": req.message}) 
    response = client.chat.completions.create(model='openai/gpt-oss-20b', messages = message)
    req.history.append({"role": "user", "content": req.message})
    req.history.append({"role": "system", "content": response.choices[0].message.content})
    return {"response": response.choices[0].message.content, "history": req.history}
