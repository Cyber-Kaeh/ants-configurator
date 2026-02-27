import math
import shutil

import questionary
from questionary import Choice
from questionary import Style as QStyle
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

MENU_STYLE = QStyle([
    ("qmark",       "fg:#5f819d bold"),
    ("question",    "fg:#ffffff bold"),
    ("answer",      "fg:#00AFFF bold"),
    ("pointer",     "fg:#00AFFF bold"),
    ("highlighted", "fg:#00AFFF bold"),
    ("text",        "fg:#d0d0d0"),
    ("instruction", "fg:#555555 italic"),
    ("separator",   "fg:#3a3a3a italic"),
])

_POINTER = "»"
_INSTRUCTION = "(↑↓ arrows, or shortcut key, Enter to confirm)"


def _build_header_panel(title: str) -> Panel:
    return Panel(
        Text(title, style="bold white", justify="center"),
        box=box.ROUNDED,
        border_style="bright_blue",
        padding=(0, 2),
    )


def _build_two_col_table(commands: dict) -> Table:
    items = [(k, label) for k, (label, _) in commands.items()]
    mid = math.ceil(len(items) / 2)
    left_col = items[:mid]
    right_col = items[mid:]

    term_width = shutil.get_terminal_size(fallback=(80, 24)).columns
    col_width = max(30, (term_width - 10) // 2)

    table = Table(
        show_header=False,
        show_edge=False,
        show_lines=False,
        box=None,
        padding=(0, 1),
        expand=False,
    )
    table.add_column(min_width=col_width, no_wrap=True)
    table.add_column(min_width=col_width, no_wrap=True)

    for i, (k, label) in enumerate(left_col):
        left_cell = f"[bold cyan]{k:>3})[/bold cyan] {label}"
        if i < len(right_col):
            rk, rlabel = right_col[i]
            right_cell = f"[bold cyan]{rk:>3})[/bold cyan] {rlabel}"
        else:
            right_cell = ""
        table.add_row(left_cell, right_cell)

    return table


class Menu:
    def __init__(
        self,
        title: str,
        commands: dict,
        startup_art=None,
        clear_on_render: bool = True,
        show_table: bool = True,
    ):
        self.title = title
        self.commands = commands
        self.startup_art = startup_art
        self._startup_shown = False
        self.clear_on_render = clear_on_render
        self.show_table = show_table

    def _render_header(self) -> None:
        console.print(_build_header_panel(self.title))
        if self.show_table and len(self.commands) >= 4:
            console.print(_build_two_col_table(self.commands))
        console.print()

    def _build_choices(self) -> list:
        choices = []
        for k, (label, _) in self.commands.items():
            choices.append(
                Choice(
                    title=label,
                    value=k,
                    shortcut_key=k if len(k) == 1 else False,
                )
            )
        return choices

    def run(self) -> None:
        while True:
            if self.clear_on_render:
                console.clear()

            # Display startup art after clear so it persists for this render
            if self.startup_art and not self._startup_shown:
                if callable(self.startup_art):
                    self.startup_art()
                else:
                    console.print(self.startup_art)
                self._startup_shown = True

            self._render_header()

            choice = questionary.select(
                "Navigate:",
                choices=self._build_choices(),
                style=MENU_STYLE,
                use_arrow_keys=True,
                use_shortcuts=True,
                use_jk_keys=False,
                use_emacs_keys=False,
                pointer=_POINTER,
                instruction=_INSTRUCTION,
            ).ask()

            if choice is None:  # Ctrl+C
                break

            self.commands[choice][1]()
