import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule

from functions import product_details, tyre_semantic_search
from tools import landing_price_tool, semantic_search_tool, tyre_description_tool

load_dotenv()

MODEL = "gpt-4.1"
MAX_ITERATIONS = 10

TOOLS = [semantic_search_tool, tyre_description_tool, landing_price_tool]

SYSTEM_PROMPT = """You are a helpful and friendly 2-wheeler tyre recommendation assistant for CEAT tyres.
Always respond in a natural, conversational tone — like a knowledgeable tyre expert talking to a customer.

Always call tyre_semantic_search first for ANY question that involves vehicles, variants, tyres, or SKUs.
Never answer from memory — the catalogue is the only source of truth.

When a user asks for tyres for a vehicle:
1. Call tyre_semantic_search with the vehicle name to retrieve matching rows from the catalogue.
2. From the returned text, identify the Front and Rear tyre rows for the requested vehicle.
   Each row has the format: category,brand,model,variant,type,recommended-sku,sku-desc,...
3. Call product_description for each SKU (front and rear) to confirm the tyre name.
4. Present the recommendation conversationally. Always state the exact variant(s) from the catalogue
   that the recommendation applies to. If multiple variants share the same tyres, list all of them.
   Include this structured block exactly:

  Applicable variants: <variant 1>, <variant 2>, ...
  Front Tyre - SKU <sku>: <tyre name>
  Rear Tyre - SKU <sku>: <tyre name>

   STRICT FORMATTING RULES:
   - Each SKU must be on its own separate line. Never put two SKUs on the same line.
   - If there are alternative tyres for a position, each goes on its own line:
       Front Tyre - SKU <sku1>: <tyre name>
       Front Tyre (Alt) - SKU <sku2>: <tyre name>
   - Do not add parenthetical variant notes inside the tyre line itself.

When a user asks about variants, models, or any vehicle catalogue information:
1. Call tyre_semantic_search with the vehicle name to retrieve matching rows.
2. Extract and list only the variants that actually appear in the catalogue results.
3. Do not add variants from your own knowledge — only report what the catalogue contains.

For all other follow-up questions (price, availability, comparisons, etc.) answer in plain natural language.
Never invent or guess SKU codes or variant names — always retrieve them from the search results.
Only call landing_price if the user explicitly asks for price or cost information.
Always write prices as "INR <amount>" — never use the rupee symbol."""


console = Console()
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

def _dispatch(tool_name: str, args: dict) -> str:
    if tool_name == "tyre_semantic_search":
        results = tyre_semantic_search(query=args["query"])
        return json.dumps(results, ensure_ascii=False)

    if tool_name == "product_description":
        details = product_details(int(args["sku"]))
        return json.dumps({
            "SKU": int(details["Material"]),
            "Description": details["Material Description"],
        })

    if tool_name == "landing_price":
        details = product_details(int(args["sku"]))
        return json.dumps({
            "SKU": int(details["Material"]),
            "NBP": details["NBP"],
            "Landing Price": round(details["Landing Price"], 2),
        })

    return json.dumps({"error": f"unknown tool: {tool_name}"})


def _action_label(name: str, args: dict, sku_names: dict) -> str:
    if name == "tyre_semantic_search":
        return f'Searching catalogue for [bold]"{args["query"]}"[/bold]'
    if name == "product_description":
        return f'Looking up tyre name for SKU [bold]{args["sku"]}[/bold]'
    if name == "landing_price":
        sku = args["sku"]
        suffix = f' ([italic]{sku_names[sku]}[/italic])' if sku in sku_names else ""
        return f'Calculating landing price for SKU [bold]{sku}[/bold]{suffix}'
    return f'Calling [bold]{name}[/bold]'


# ---------------------------------------------------------------------------
# ReAct loop
# ---------------------------------------------------------------------------

def run_turn(user_query: str, messages: list, sku_names: dict) -> str:
    messages.append({"role": "user", "content": user_query})

    for _ in range(MAX_ITERATIONS):
        with console.status("[dim]Thinking...[/dim]", spinner="dots"):
            response = _client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

        message = response.choices[0].message

        # Final answer — no tool calls
        if not message.tool_calls:
            messages.append({"role": "assistant", "content": message.content})
            return message.content

        messages.append(message.model_dump(exclude_unset=True, exclude_none=True))

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            label = _action_label(name, args, sku_names)

            with console.status(f"[cyan]{label}...[/cyan]", spinner="dots"):
                result = _dispatch(name, args)

            console.print(f"  [cyan]•[/cyan] {label}")

            # Cache tyre name so landing_price label can include it
            if name == "product_description":
                parsed = json.loads(result)
                sku_names[str(args["sku"])] = parsed.get("Description", "")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    return "Reached maximum iterations without a final answer."


# ---------------------------------------------------------------------------
# Interactive CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    console.print(Rule("[bold blue]CEAT 2W Tyre Recommendation Agent[/bold blue]"))
    console.print("[dim]Type 'exit' to quit[/dim]\n")

    session_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    session_sku_names: dict[str, str] = {}

    while True:
        try:
            query = Prompt.ask("[bold yellow]You[/bold yellow]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not query.strip():
            continue
        if query.strip().lower() in {"exit", "quit", "q"}:
            console.print("[dim]Goodbye.[/dim]")
            break

        answer = run_turn(query.strip(), session_messages, session_sku_names)
        console.print(Panel(
            answer,
            title="[bold green]CEAT Assistant[/bold green]",
            border_style="green",
            padding=(1, 2),
        ))
        console.print()
