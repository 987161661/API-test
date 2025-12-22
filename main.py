import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from config.settings import settings
from core.schema import ChatMessage
from providers.openai_compatible import OpenAICompatibleProvider

app = typer.Typer()
console = Console()

async def run_test(model: str):
    provider = OpenAICompatibleProvider(
        api_key=settings.TEST_API_KEY,
        base_url=settings.TEST_API_BASE_URL
    )

    messages = [
        ChatMessage(role="user", content="Hello, please introduce yourself in 20 words.")
    ]

    console.print(f"[bold blue]Starting benchmark for model: {model}[/bold blue]")
    console.print(f"API Base URL: {settings.TEST_API_BASE_URL}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="Running inference...", total=None)
        result = await provider.run_benchmark(model, messages)

    # Output Results
    table = Table(title="Benchmark Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    if result.success:
        table.add_row("Status", "[green]Success[/green]")
        table.add_row("Model", result.model)
        table.add_row("TTFT (ms)", f"{result.ttft_ms} ms")
        table.add_row("Total Latency (ms)", f"{result.total_latency_ms} ms")
        table.add_row("Output Tokens (approx)", str(result.output_tokens))
        table.add_row("TPS (tokens/s)", f"{result.tps}")
        
        console.print(table)
        console.print("\n[bold]Response:[/bold]")
        console.print(result.response_content)
    else:
        table.add_row("Status", "[red]Failed[/red]")
        table.add_row("Error", result.error_message)
        console.print(table)

@app.command()
def main(model: str = typer.Option(settings.DEFAULT_MODEL, help="Model name to test")):
    """
    Run LLM API Benchmark
    """
    asyncio.run(run_test(model))

if __name__ == "__main__":
    app()
