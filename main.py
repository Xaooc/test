# main.py
"""
Простой stateless chat-graph с инструментом get_current_time
Запуск: langgraph dev
"""

import datetime
import json
import os
from typing import Dict, List, Literal, TypedDict, Union

import openai
from langgraph.graph import StateGraph


def get_current_time() -> Dict[str, str]:
    """Return the current UTC time in ISO-8601 format."""
    return {"utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"}


Message = TypedDict(
    "Message",
    {
        "role": Literal["user", "assistant", "tool", "system"],
        "content": Union[str, None],
        "tool_calls": Union[List[Dict], None],
        "tool_call_id": Union[str, None],
    },
    total=False,
)

GraphState = TypedDict("GraphState", {"messages": List[Message]})


client = openai.OpenAI()

TOOL_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Получить текущее время в формате UTC ISO-8601",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
    }
]


def agent_node(state: GraphState) -> GraphState:
    """LLM ответ с возможностью вызова функции"""
    if "messages" not in state:
        state["messages"] = []
    
    # Добавляем системное сообщение если его нет
    if not state["messages"] or state["messages"][0].get("role") != "system":
        system_message = {
            "role": "system",
            "content": "Ты ассистент на русском языке. Используй функцию get_current_time когда пользователь спрашивает про время."
        }
        state["messages"].insert(0, system_message)
    
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        messages=state["messages"],
        tools=TOOL_SPEC,
        tool_choice="auto",
    )
    
    message = response.choices[0].message
    msg_dict = {
        "role": "assistant",
        "content": message.content,
    }
    
    if message.tool_calls:
        msg_dict["tool_calls"] = [
            {
                "id": call.id,
                "type": call.type,
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments,
                }
            }
            for call in message.tool_calls
        ]
    
    state["messages"].append(msg_dict)
    return state


def tool_node(state: GraphState) -> GraphState:
    """Выполнение функции get_current_time"""
    assistant_msg = state["messages"][-1]
    for call in assistant_msg.get("tool_calls", []):
        if call["function"]["name"] == "get_current_time":
            result = get_current_time()
            state["messages"].append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(result),
                }
            )
    return state


def route(state: GraphState) -> str:
    """Маршрутизация: если есть tool_calls - вызываем функцию, иначе завершаем"""
    last = state["messages"][-1]
    return "call_tool" if last["role"] == "assistant" and last.get("tool_calls") else "end"


def input_node(state: GraphState) -> GraphState:
    """Обработка входящего сообщения от langgraph dev"""
    if isinstance(state.get("messages"), str):
        user_message = state["messages"]
        state["messages"] = [{"role": "user", "content": user_message}]
    elif not state.get("messages"):
        state["messages"] = []
    
    return state


# Создание графа
builder = StateGraph(GraphState)
builder.add_node("input", input_node)
builder.add_node("agent", agent_node)
builder.add_node("get_current_time", tool_node)

builder.set_entry_point("input")
builder.add_edge("input", "agent")
builder.add_conditional_edges(
    "agent",
    route,
    {
        "call_tool": "get_current_time",
        "end": "__end__",
    },
)
builder.add_edge("get_current_time", "agent")

graph = builder.compile()


if __name__ == "__main__":
    print("Chat запущен. 'exit' для выхода.")
    state: GraphState = {"messages": []}
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            break
            
        state["messages"].append({"role": "user", "content": user_input})
        state = graph.invoke(state)
        
        # Последний ответ ассистента
        for msg in reversed(state["messages"]):
            if msg["role"] == "assistant" and msg.get("content"):
                print(f"Bot: {msg['content']}\n")
                break
