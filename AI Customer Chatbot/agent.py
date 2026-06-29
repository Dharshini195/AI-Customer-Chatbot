from fastapi import FastAPI, HTTPException
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain.tools import tool
from langchain.agents import create_agent
from pydantic import BaseModel
from rag import retreiever_rag
from tools import order_status, cancel_order, create_ticket
from dotenv import load_dotenv
import asyncio
from crud import add_message, get_messages
from prompts import *
import json

load_dotenv()

app = FastAPI()

class ChatRequest(BaseModel):
    session_id : int
    query : str

memory_history = {}

llm = ChatGroq(model="llama-3.3-70b-versatile")

# Chain for normal conversation + RAG

messages =[ 
    ("system" , "You are an AI Customer Agent. You help user queries in a friendly, calm way. Stay in your role throughout the conversation."),
    ("system", "Relevant Details about the company policies : {context}"),
    ("system","Conversation history:\n{history}"),
    ("human", "{query}")
]

prompt = ChatPromptTemplate.from_messages(messages)
chain = prompt | llm | StrOutputParser()

#Agent to perform tools 

def get_order_status(order_id : str):
    """
    Get the status of the order using the order_id 
    """
    result = order_status(order_id)
    print(f"DEBUG order_status returned: {result}")
    return result

def get_order_cancel(order_id : str):
    """
    Cancel the order using the order_id
    """
    result = cancel_order(order_id)
    print(f"DEBUG cancel_order returned: {result}")
    return result

def get_create_ticket(order_id : str):
    """
    Create an ticket for the order id
    """
    result = create_ticket(order_id)
    print(f"DEBUG create_ticket returned: {result}")
    return result

def search_policy(query : str):
    """Look up company policy. Call with: 'cancellation policy',
    'refund policy', or 'return policy' or similar example. Input: policy topic string."""

    relevant_docs = retreiever_rag(query)
    context = "\n".join([doc.page_content for doc in relevant_docs])
    return context
    
    
def get_history(session_id: int):
    messages = get_messages(session_id, limit=20)

    # Convert to LangChain message format
    history = []
    for msg in messages:
        if msg["role"] == "human":
            history.append(HumanMessage(content=msg["content"]))
        else:
            history.append(AIMessage(content=msg["content"]))

    return history

def get_history_recent(session_id: int, n: int = 10):
    messages = get_messages(session_id, limit=n)

    return [
        f"{msg['role']}: {msg['content']}"
        for msg in messages
    ]

def update_memory(session_id: int, user_msg: str, ai_msg: str):
    add_message(session_id, "human", user_msg)
    add_message(session_id, "ai", ai_msg)

def route_decision(query):
    router_prompt = f"""
    Classify the user query into one of these categories:

1. "tool" → if user wants to perform an action (order status, cancel, ticket)
2. "rag" → if user asks about policies, info, knowledge and others

Query: {query}

Only return one word: tool / rag 
"""
    response = llm.invoke(router_prompt)
    return response.content

def summarize_history(history):
    recent = history[-4:]
    summarize_prompt = SUMMARIZE_PROMPT.format(history=history)
    response = llm.invoke(summarize_prompt)
    return [response.content] + recent


def extract_entities(conversation: str) -> dict:
    result = llm.invoke(f"""
Extract key facts from this support conversation as JSON:
{{
    "order_ids": [],
    "customer_issue": "",
    "actions_taken": [],
    "current_status": ""
}}
Only include facts explicitly mentioned. Output only JSON.

Conversation: {conversation}
""").content
    print(result)
    return result


def build_prompt():
    prompt_template = MAIN_PROMPT
    return prompt_template

def agent_support(query : str, history : str):

    prompt_template = build_prompt()

    # tools = [get_order_status, get_create_ticket, get_order_cancel,search_policy]

    # llm_with_tools = llm.bind_tools(tools,tool_choice="auto")
    
    # agent =create_agent(model=llm_with_tools, tools=tools, system_prompt=prompt_template)

    # ✅ Bake history directly into system prompt

    system_content = prompt_template + f"""
━━━━━━━━━━━━━━━━━━━━━━━━
💬 CONVERSATION HISTORY
━━━━━━━━━━━━━━━━━━━━━━━━
{history}
"""

    messages = [
        SystemMessage(content=system_content),  # ✅ one clean system message
        HumanMessage(content=query)             # ✅ current user query
    ]
    TOOLS_MAP = {
    "get_order_status": get_order_status,
    "get_order_cancel": get_order_cancel,
    "get_create_ticket": get_create_ticket,
    "search_policy": search_policy
    }

    for i in range(5):
        response = llm.invoke(messages)
        raw = response.content.strip()

        print(f"\n--- Iteration {i+1} ---")
        print(f"LLM raw output: {raw}")

        # ── Parse JSON response ───────────────────────────
        try:
            # Strip markdown code blocks if LLM adds them
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            
            parsed = json.loads(raw.strip())
            action = parsed["action"]
            inputs = parsed["input"]

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Parse error: {e}")
            # If LLM returned plain text, treat as final answer
            return raw

        # ── Final answer → return to user ─────────────────
        if action == "final_answer":
            return inputs["response"]

        # ── Tool call → execute and feed result back ───────
        if action in TOOLS_MAP:
            tool_fn = TOOLS_MAP[action]
            
            try:
                tool_result = tool_fn(**inputs)
                print(f"Tool result: {tool_result}")
            except Exception as e:
                tool_result = f"Error: {str(e)}"

            # Add LLM decision + tool result to message history
            messages.append(AIMessage(content=response.content))
            messages.append(HumanMessage(
                content=f"Tool '{action}' returned: {tool_result}\n"
                        f"Now continue based on this result."
            ))

        else:
            # Unknown action
            return "I'm having trouble processing your request. Please try again."

    return "I wasn't able to complete your request. A support agent will follow up."


@app.get("/")
def home():
    return "Welcome to AI Customer Agent! Go to /chat to ask your queries to our Agent"


@app.post("/chat")
async def chat_with_ai(request : ChatRequest):

    session_id = request.session_id
    query = request.query

    if not query.strip():
        raise HTTPException(status_code=400,detail="User query is empty")

    response = "I'm sorry , I can't understand your query! Try back later :( "

    full_history = get_history(session_id)
    conversation_text = "\n".join(
    [msg.content for msg in full_history]
    )

    # route = route_decision(query)
    # history= summarize_history(full_history)
    # print(f"History : {full_history}")
    if len(full_history) != 0:

        entities = extract_entities(conversation_text)
        recent_msg = "\n".join(get_history_recent(session_id))

        history = f"""
    Earlier conversation summary entities:
    {entities}

    Recent messages:
    {recent_msg}
    """
    else:
        history = ""

    response = agent_support(query,history)
        
    update_memory(session_id,query,response)

    return {"session_id" : session_id, "response" : response}

@app.get("/history/{session_id}")
def conversation_history(session_id : int):
    history = get_history(session_id)
    return {"session_id" : session_id,"response" : history}
