import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule

from functions import product_details, tyre_semantic_search, tyre_size_search
from tools import landing_price_tool, semantic_search_tool, tyre_description_tool, tyre_size_search_tool

load_dotenv()

MODEL = "gpt-4.1"
MAX_ITERATIONS = 10

TOOLS = [semantic_search_tool, tyre_description_tool, landing_price_tool, tyre_size_search_tool]

SYSTEM_PROMPT = """You are a helpful and friendly 2-wheeler tyre recommendation assistant for CEAT tyres.
Always respond in a natural, conversational tone — like a knowledgeable tyre expert talking to a customer.

Always call tyre_semantic_search first for ANY question that involves vehicles, variants, tyres, or SKUs.
Never answer from memory — the catalogue is the only source of truth.

When a user asks for tyres for a vehicle:
1. Call tyre_semantic_search with the vehicle name to retrieve matching entries from the catalogue.
2. Each result is one vehicle variant. The text format is:
     <Brand> <Model> <Variant>
     Front Tyre — SKU <sku>: <description> | Alt SKUs: <sku1>, <sku2>, ...
     Rear Tyre — SKU <sku>: <description> | Alt SKUs: <sku1>, <sku2>, ...
3. If the results contain multiple distinct variants of the same model (e.g. Splendor 100 cc, Splendor+, Splendor I Smart), do NOT guess:
   - If the user asked for a specific variant, present only that one.
   - If the user asked for ALL variants, present every variant found in the results — do NOT call product_description in this case, use the tyre name already present in the search result text.
   - Otherwise, list the available variants and ask the user which one they have.
4. For a single confirmed variant, call product_description for the front and rear recommended SKUs to confirm the tyre name.
5. Present the recommendation conversationally. Always state the exact variant(s) from the catalogue
   that the recommendation applies to. If multiple variants share the same tyres, group them together.
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
   - When presenting all variants, group variants that share the same front and rear SKUs under one block.

When a user asks about variants, models, or any vehicle catalogue information:
1. Call tyre_semantic_search with the vehicle name to retrieve matching rows.
2. Extract and list only the variants that actually appear in the catalogue results.
3. Do not add variants from your own knowledge — only report what the catalogue contains.

When a user asks what tyres are available in a specific size (e.g. "2.75-18", "80/100-17", "100/90-17"):
1. Call tyre_size_search with the size string to get all matching CEAT SKUs.
2. Present the results as a list showing SKU (orange), tyre name (blue), and landing price (green).
3. If the user also mentions a vehicle, call tyre_semantic_search first to get the recommended SKU, then offer the size search results as the full range available in that size.

When a user asks for alternate tyres or "other options" for a vehicle:
1. The search result text already lists Alt SKUs for each position (e.g. "Alt SKUs: 100226, 103202").
2. Call product_description for each alt SKU to get its tyre name, then present them as alternatives.
3. Use the same structured block format, labelling them as Front Tyre (Alt) / Rear Tyre (Alt).

For all other follow-up questions (price, availability, comparisons, etc.) answer in plain natural language.
Never invent or guess SKU codes or variant names — always retrieve them from the search results.
Only call landing_price if the user explicitly asks for price or cost information.
When presenting price information, always show each tyre on its own line in this exact format:
  SKU <sku>: <tyre name>
  Landing Price: INR <integer>
Always write prices as "INR <integer>" — never use the rupee symbol, never show decimal points, always round to the nearest whole number."""


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
        if details is None:
            return json.dumps({"error": f"SKU {args['sku']} not found in price list"})
        return json.dumps({
            "SKU": int(details["Material"]),
            "Description": details["Material Description"],
        })

    if tool_name == "tyre_size_search":
        results = tyre_size_search(size=args["size"])
        return json.dumps(results, ensure_ascii=False)

    if tool_name == "landing_price":
        details = product_details(int(args["sku"]))
        if details is None:
            return json.dumps({"error": f"SKU {args['sku']} not found in price list"})
        return json.dumps({
            "SKU": int(details["Material"]),
            "NBP": int(round(details["NBP"])),
            "Landing Price": int(round(details["Landing Price"])),
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
    if name == "tyre_size_search":
        return f'Searching all CEAT tyres in size [bold]{args["size"]}[/bold]'
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
