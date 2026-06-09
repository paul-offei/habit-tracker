"""
Command-Line Interface (CLI) for the Habit Tracker.

This module acts as the presentation layer. It utilizes Typer for routing
commands and Rich for rendering beautiful terminal components. It interacts
with the application strictly through the HabitRepository.
"""

from typing import Optional
import uuid
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Import our infrastructure and domain layers
from habit_tracker.habit import Habit
from habit_tracker.period import Periodicity
from habit_tracker.database import init_db, SessionLocal
from habit_tracker.repository import HabitRepository
from habit_tracker.seed_habits import load_template_habits
from habit_tracker.healthcare_habits import load_healthcare_data
from habit_tracker.status import HabitStatus
from habit_tracker.analytics import (
    calculate_longest_streak, 
    calculate_longest_streak_overall,
    filter_active_habits,         
    filter_by_periodicity,
    filter_deleted_habits         
)

# Initialize CLI application and UI tools
app = typer.Typer(help="A minimal, beautiful CLI Habit Tracker.")
console = Console()

# Initialize Database and Repository
init_db()
session = SessionLocal()
repository = HabitRepository(session)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Acts as the entry point. Displays a welcome message if no command is passed.
    """
    if ctx.invoked_subcommand is None:
        welcome_text = Text(
            "Welcome to the CLI Habit Tracker!\n\n"
            "Build robust habits, track your streaks, and analyze your progress.\n"
            "Use the --help flag at any time to see available commands.",
            justify="center",
            style="cyan"
        )
        panel = Panel(
            welcome_text,
            title="[bold magenta]🚀 Habit Tracker[/bold magenta]",
            subtitle="[dim]Domain-Driven Design Edition[/dim]",
            expand=False,
            border_style="magenta"
        )
        console.print("\n")
        console.print(panel)
        console.print("\n")

@app.command(name="predefined-habits")
def load_predefined_healthcare_habits():
    """
    Load predefined healthcare habits with 4 weeks of historical tracking data.
    """
    console.print("[cyan]Initializing healthcare test environment...[/cyan]")
    
    with console.status(
        "[bold cyan]Generating 4 weeks of operational data...[/bold cyan]", 
        spinner="dots"
    ):
        # We pass the globally instantiated repository into the loader
        load_healthcare_data(repository)
        
    # Render a beautiful success panel
    console.print("\n")
    console.print(Panel(
        "[bold green]✔ Healthcare Seed Data Loaded![/bold green]\n\n"
        "40 operational habits and 640 historical check-offs have been added.\n"
        "Run [bold cyan]log-check-off-by[/bold cyan] or [bold cyan] best-streak/streak [ID][/bold cyan] to analyze the data.",
        border_style="green",
        expand=False
    ))
    console.print("\n")

@app.command(name="seed-habits")
def load_common_templates():
    """
    Load a set of common, predefined habits for easy onboarding (no tracking history).
    """
    with console.status(
        "[bold cyan]Loading predefined templates...[/bold cyan]", 
        spinner="dots"
    ):
        load_template_habits(repository)
        
    console.print(
        "[bold green]✔ Success![/bold green] "
        "Template habits have been added to your tracker. Run 'list' to see them."
    )

@app.command(name="log-habits")
def list_habits():
    """
    View all currently tracked habits in a beautiful table format.
    """
    habits = repository.list_all()

    if not habits:
        console.print("[yellow]No habits found. Use 'seed-habits' to generate some or create one manually.[/yellow]")
        return

    # Create a Rich Table
    table = Table(
        title="[bold]Your Habits[/bold]",
        show_header=True, 
        header_style="bold magenta",
        border_style="dim"
    )

    # Define columns
    table.add_column("ID", style="dim", width=10)
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Periodicity", justify="center")
    table.add_column("Status", justify="center")
    table.add_column("Created At", justify="right", style="dim")

    # Populate rows
    for habit in habits:
        # Determine status color dynamically
        status_color = "green" if habit.status == HabitStatus.ACTIVE else "yellow" if habit.status == HabitStatus.PAUSED else "red"
        
        table.add_row(
            str(habit.id)[:8],  # Truncate UUID for aesthetics
            habit.name,
            habit.description,
            habit.periodicity.value.capitalize(),
            f"[{status_color}]{habit.status.value.capitalize()}[/{status_color}]",
            habit.created_at.strftime("%Y-%m-%d %H:%M") # Clean date format
        )

    console.print("\n")
    console.print(table)
    console.print("\n")

def _resolve_short_id(short_id: str) -> uuid.UUID:
    """
    Helper function to resolve a user-provided short ID (e.g., 'f4a2b1c9')
    into a full UUID by scanning the currently tracked habits.
    """
    habits = repository.list_all()
    matches = [h for h in habits if str(h.id).startswith(short_id)]
    
    if not matches:
        console.print(f"[bold red]Error:[/bold red] No habit found starting with '{short_id}'.")
        raise typer.Exit(code=1)
    if len(matches) > 1:
        console.print(f"[bold red]Error:[/bold red] Ambiguous ID. '{short_id}' matches multiple habits.")
        raise typer.Exit(code=1)
        
    return matches[0].id


@app.command(name="create-habit")
def create_habit(
    name: str = typer.Option(..., prompt="Habit Name", help="The display name of the habit."),
    description: str = typer.Option("", prompt="Description (optional)", help="A short explanation of the task."),
    periodicity: Periodicity = typer.Option(
        ..., 
        prompt="Periodicity, eg: ", 
        case_sensitive=False,
        help="How often the habit should be completed."
    )
):
    """
    Create a brand new habit interactively.
    """
    try:
        new_habit = Habit(
            name=name,
            description=description,
            periodicity=periodicity
        )
        saved_habit = repository.save(new_habit)
        
        console.print("\n")
        console.print(Panel(
            f"[bold green]Habit Created Successfully![/bold green]\n\n"
            f"[b]Name:[/b] {saved_habit.name}\n"
            f"[b]Periodicity:[/b] {saved_habit.periodicity.value.capitalize()}\n"
            f"[b]ID:[/b] {str(saved_habit.id)[:8]}",
            border_style="green",
            expand=False
        ))
    except Exception as e:
        console.print(f"[bold red]Validation Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command(name="check-off")
def check_off_habit(
    short_id: str = typer.Argument(
        ..., 
        help="The ID (or first few characters) of the habit to complete."
    )
):
    """
    Mark a habit as completed for the current period.
    """
    full_id = _resolve_short_id(short_id)
    habit = repository.get_by_id(full_id)
    assert habit is not None
    
    try:
        completion = repository.record_completion(full_id)
        
        time_formatted = completion.completed_at.strftime("%Y-%m-%d %H:%M")
        console.print(f"[bold green]✔ Checked off:[/bold green] '{habit.name}' at {time_formatted} UTC")
        
    except ValueError as e:
        # Catch our domain rules (e.g., trying to check off a paused habit)
        console.print(Panel(
            f"[bold red]Cannot Complete Habit[/bold red]\n\n{str(e)}",
            border_style="red",
            expand=False
        ))
        raise typer.Exit(code=1)



@app.command(name="log-check-off-by")
def view_log_by_period(
    period: Periodicity = typer.Argument(
        ..., 
        help="The periodicity to filter the completion log by (e.g., daily, weekly)."
    )
):
    """
    View a master log of check-offs, filtered strictly by a specific periodicity.
    """
    with console.status(f"[cyan]Fetching log for {period.value} habits...[/cyan]", spinner="dots"):
        # 1. Fetch the optimized global log (JOIN query)
        all_records = repository.get_all_completions_with_habits()
        
        # 2. Functionally filter the records where the Habit matches the requested period
        filtered_records = [
            (comp, habit) for comp, habit in all_records 
            if habit.periodicity == period
        ]

    if not filtered_records:
        console.print(f"\n[yellow]No check-offs found for {period.value} habits.[/yellow]\n")
        raise typer.Exit()

    # 3. Build the Rich Table
    table = Table(
        title=f"[bold cyan]Completion Log: {period.value.capitalize()} Habits[/bold cyan]",
        show_header=True, 
        header_style="bold magenta",
        border_style="dim"
    )

    # Define columns
    table.add_column("Completion ID", style="dim", width=13)
    table.add_column("Habit Name", style="cyan")
    table.add_column("Habit Created At", style="dim", justify="center")
    table.add_column("Time Checked Off (UTC)", style="green", justify="right")

    # Populate rows
    for comp, habit in filtered_records:
        table.add_row(
            str(comp.id)[:8],
            habit.name,
            habit.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            comp.completed_at.strftime("%Y-%m-%d %H:%M:%S")
        )

    # Render to terminal
    console.print("\n")
    console.print(table)
    
    console.print(f"  [bold]Total {period.value.capitalize()} Check-offs:[/bold] {len(filtered_records)}")
    console.print("\n")

# =====================================================================
# FOCUSED ANALYTICS COMMANDS
# =====================================================================

def _render_habit_table(habits: list[Habit], title: str):
    """Internal helper to render a beautiful table for filtered lists."""
    if not habits:
        console.print(f"\n[yellow]No habits found for: {title}[/yellow]\n")
        raise typer.Exit()

    table = Table(title=f"[bold cyan]{title}[/bold cyan]", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Name", style="cyan")
    table.add_column("Periodicity", justify="center")
    table.add_column("Status", justify="center")

    for habit in habits:
        status_color = "green" if habit.status == HabitStatus.ACTIVE else "yellow" if habit.status == HabitStatus.PAUSED else "red"
        table.add_row(
            str(habit.id)[:8],
            habit.name,
            habit.periodicity.value.capitalize(),
            f"[{status_color}]{habit.status.value.capitalize()}[/{status_color}]"
        )
    
    console.print("\n")
    console.print(table)
    console.print("\n")


@app.command(name="active")
def list_active_habits():
    """
    Return a list of all currently tracked (ACTIVE) habits.
    """
    all_habits = repository.list_all()
    active_habits = filter_active_habits(all_habits)
    _render_habit_table(active_habits, "Currently Tracked Habits")


@app.command(name="period")
def list_by_period(
    period: Periodicity = typer.Argument(
        ..., 
        help="The periodicity to filter by (e.g., daily, weekly)."
    )
):
    """
    Return a list of all habits with the specified periodicity.
    """
    all_habits = repository.list_all()
    filtered_habits = filter_by_periodicity(all_habits, period)
    _render_habit_table(filtered_habits, f"Habits with Periodicity: {period.value.capitalize()}")


@app.command(name="best-streak")
def show_overall_longest_streak():
    """
    Return the absolute longest run streak out of all defined habits.
    """
    with console.status("[cyan]Calculating global streaks...[/cyan]", spinner="dots"):
        habits = repository.list_all()
        if not habits:
            console.print("[yellow]No habits found in the database.[/yellow]")
            raise typer.Exit()

        completions_map = {h.id: repository.get_completions(h.id) for h in habits}
        overall_max = calculate_longest_streak_overall(habits, completions_map)
        
        # Identify which habits actually hold this record
        champions = []
        for h in habits:
            if calculate_longest_streak(h, completions_map[h.id]) == overall_max and overall_max > 0:
                champions.append(h.name)

    champ_text = f"\n[dim]Held by: {', '.join(champions)}[/dim]" if champions else ""

    panel = Panel(
        f"[bold white text-align=center]The longest streak across all habits is:[/bold white text-align=center]\n\n"
        f"[bold green text-align=center]🔥 {overall_max} consecutive periods 🔥[/bold green text-align=center]"
        f"{champ_text}",
        title="[bold yellow]Global Champion[/bold yellow]",
        border_style="yellow",
        expand=False,
        padding=(1, 4)
    )
    console.print("\n")
    console.print(panel)
    console.print("\n")


@app.command(name="streak")
def show_habit_streak(
    short_id: str = typer.Argument(
        ..., 
        help="The ID (or first few characters) of the habit to analyze."
    )
):
    """
    Return the longest run streak for a specifically given habit.
    """
    full_id = _resolve_short_id(short_id)
    habit = repository.get_by_id(full_id)
    assert habit is not None
    completions = repository.get_completions(full_id)
    
    streak = calculate_longest_streak(habit, completions)
    
    panel = Panel(
        f"[bold white]Habit:[/bold white] {habit.name}\n"
        f"[bold white]Target:[/bold white] {habit.periodicity.value.capitalize()}\n\n"
        f"[bold cyan]Longest Streak:[/bold cyan] [bold green]{streak}[/bold green] periods",
        title="[bold blue]Habit Streak[/bold blue]",
        border_style="blue",
        expand=False,
        padding=(1, 4)
    )
    console.print("\n")
    console.print(panel)
    console.print("\n")

@app.command(name="update-habit")
def update_existing_habit(
    short_id: str = typer.Argument(
        ..., 
        help="The ID (or first few characters) of the habit to update."
    ),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="New name for the habit."
    ),
    description: Optional[str] = typer.Option(
        None, "--desc", "-d", help="New description for the habit."
    ),
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="New status (active, paused, archived, deleted)."
    )
):
    """
    Update an existing habit's name, description, or pause status using flags.
    """
    if name is None and description is None and status is None:
        console.print("[yellow]No updates provided. Please pass --name, --desc, or --status.[/yellow]")
        raise typer.Exit()

    # 1. Manually and safely validate the status string into our Enum
    status_enum = None
    if status is not None:
        try:
            # Force lowercase to ensure it matches the Enum values perfectly
            status_enum = HabitStatus(status.lower())
        except ValueError:
            console.print(f"[bold red]Error:[/bold red] '{status}' is not a valid status.")
            console.print("Valid options are: active, paused, archived, deleted.")
            raise typer.Exit(code=1)

    full_id = _resolve_short_id(short_id)

    try:
        # 2. Pass the safely converted enum to the repository
        updated_habit = repository.update_habit(
            habit_id=full_id,
            name=name,
            description=description,
            status=status_enum
        )

        if updated_habit.status == HabitStatus.ACTIVE:
            status_color = "green"
        elif updated_habit.status == HabitStatus.PAUSED:
            status_color = "yellow"
        else:
            status_color = "red"

        console.print("\n")
        console.print(Panel(
            f"[bold green]✔ Habit Updated Successfully![/bold green]\n\n"
            f"[b]Name:[/b] {updated_habit.name}\n"
            f"[b]Description:[/b] {updated_habit.description}\n"
            f"[b]Status:[/b] [{status_color}]{updated_habit.status.value.capitalize()}[/{status_color}]\n"
            f"[b]ID:[/b] {str(updated_habit.id)[:8]}",
            border_style="green",
            expand=False
        ))
        console.print("\n")

    except ValueError as e:
        console.print(f"[bold red]Update Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)



@app.command(name="delete-habit")
def delete_existing_habit(
    short_id: str = typer.Argument(
        ..., 
        help="The ID (or first few characters) of the habit to delete."
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Bypass the safety confirmation prompt."
    )
):
    """
    Safely remove a habit. Protects historical data by archiving if necessary.
    """
    # 1. Resolve the ID and fetch the habit so we know its name
    full_id = _resolve_short_id(short_id)
    habit_to_delete = repository.get_by_id(full_id)
    assert habit_to_delete is not None

    # 2. Safety Check (unless --force is passed)
    if not force:
        console.print(f"\n[bold red]Warning:[/bold red] You are about to delete the habit '[cyan]{habit_to_delete.name}[/cyan]'.")
        confirm = typer.confirm("Are you sure you want to proceed?")
        if not confirm:
            console.print("[yellow]Deletion aborted.[/yellow]")
            raise typer.Abort()

    try:
        # 3. Execute the deletion through our smart domain logic
        result_habit = repository.delete_habit(full_id)

        # 4. Provide transparent feedback based on what the Domain layer actually did
        console.print("\n")
        if result_habit.status == HabitStatus.ARCHIVED:
            console.print(Panel(
                f"[bold yellow]Historical Data Protected[/bold yellow]\n\n"
                f"Habit '[cyan]{habit_to_delete.name}[/cyan]' has existing check-off history.\n"
                f"Its status has been changed to [bold]ARCHIVED[/bold] to protect your analytics.",
                border_style="yellow",
                expand=False
            ))
        else:
            console.print(Panel(
                f"[bold red]Permanently Deleted[/bold red]\n\n"
                f"Habit '[cyan]{habit_to_delete.name}[/cyan]' had no check-off history.\n"
                f"It has been completely [bold]DELETED[/bold] from the active tracker.",
                border_style="red",
                expand=False
            ))
        console.print("\n")

    except ValueError as e:
        console.print(f"[bold red]Delete Error:[/bold red] {str(e)}")
        raise typer.Exit(code=1)

@app.command(name="log-bin")
def list_deleted_habits():
    """
    View a list of all permanently deleted habits (Recycle Bin).
    """
    # 1. Fetch the entire database
    all_habits = repository.list_all()
    
    # 2. Functionally filter for only DELETED status
    deleted_habits = filter_deleted_habits(all_habits)
    
    # 3. Render using the shared UI helper
    _render_habit_table(deleted_habits, "🗑️ Deleted Habits (Recycle Bin)")