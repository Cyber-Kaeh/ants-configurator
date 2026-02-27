import questionary
from questionary import Choice
from questionary import Style as QStyle
from rich import box
from rich.console import Console
from rich.panel import Panel
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


class Menu:
    def __init__(self, title, commands, startup_art=None):
        self.title = title
        self.commands = commands
        self.startup_art = startup_art
        self._startup_shown = False

    def run(self):
        while True:
            console.clear()

            if self.startup_art and not self._startup_shown:
                if callable(self.startup_art):
                    self.startup_art()
                else:
                    console.print(self.startup_art)
                self._startup_shown = True

            console.print(Panel(
                Text(self.title, style="bold white", justify="center"),
                box=box.ROUNDED,
                border_style="bright_blue",
                padding=(0, 2),
            ))

            choices = [
                Choice(
                    title=label,
                    value=k,
                    shortcut_key=k if len(k) == 1 else False,
                )
                for k, (label, _) in self.commands.items()
            ]

            choice = questionary.select(
                "Navigate:",
                choices=choices,
                style=MENU_STYLE,
                use_arrow_keys=True,
                use_shortcuts=True,
                use_jk_keys=False,
                use_emacs_keys=False,
                pointer="»",
                instruction="(↑↓ arrows, or shortcut key)",
            ).ask()

            if choice is None:  # Ctrl+C
                break

            self.commands[choice][1]()
