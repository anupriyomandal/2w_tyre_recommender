import asyncio
import json
import os
import uuid
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel

from agent import SYSTEM_PROMPT, TOOLS, _dispatch

load_dotenv()

app = FastAPI(title="CEAT Tyre Advisor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.get("/")
async def health():
    return {"status": "ok"}
MODEL = "gpt-4.1"
MAX_ITERATIONS = 10

# session_id -> {"messages": [...], "sku_names": {...}}
_sessions: dict[str, dict] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


def _plain_label(name: str, args: dict, sku_names: dict) -> str:
    if name == "tyre_semantic_search":
        return f'Searching catalogue for "{args["query"]}"'
    if name == "product_description":
        return f'Looking up tyre name for SKU {args["sku"]}'
    if name == "landing_price":
        sku = str(args["sku"])
        suffix = f' ({sku_names[sku]})' if sku in sku_names else ""
        return f'Calculating landing price for SKU {sku}{suffix}'
    if name == "tyre_size_search":
        return f'Searching all CEAT tyres in size {args["size"]}'
    return f'Calling {name}'


def _emit(obj: dict) -> str:
    return json.dumps(obj) + "\n"


async def _stream(session_id: str, user_message: str) -> AsyncGenerator[str, None]:
    session = _sessions.setdefault(session_id, {
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
        "sku_names": {},
    })
    messages = session["messages"]
    sku_names = session["sku_names"]

    messages.append({"role": "user", "content": user_message})

    for _ in range(MAX_ITERATIONS):
        response = await asyncio.to_thread(
            _client.chat.completions.create,
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        message = response.choices[0].message

        if not message.tool_calls:
            messages.append({"role": "assistant", "content": message.content})
            yield _emit({"type": "answer", "content": message.content})
            yield _emit({"type": "done"})
            return

        messages.append(message.model_dump(exclude_unset=True, exclude_none=True))

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            label = _plain_label(name, args, sku_names)
            call_id = tool_call.id

            yield _emit({"type": "tool_start", "id": call_id, "tool": name, "label": label})

            result = await asyncio.to_thread(_dispatch, name, args)

            if name == "product_description":
                try:
                    parsed = json.loads(result)
                    sku_names[str(args["sku"])] = parsed.get("Description", "")
                except Exception:
                    pass

            yield _emit({"type": "tool_done", "id": call_id, "tool": name, "label": label})

            messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": result,
            })

    yield _emit({"type": "error", "message": "Reached maximum iterations."})
    yield _emit({"type": "done"})


@app.post("/chat")
async def chat(body: ChatRequest):
    session_id = body.session_id or str(uuid.uuid4())
    return StreamingResponse(
        _stream(session_id, body.message),
        media_type="application/x-ndjson",
        headers={"X-Session-Id": session_id, "Cache-Control": "no-cache"},
    )


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    _sessions.pop(session_id, None)
    return {"ok": True}
