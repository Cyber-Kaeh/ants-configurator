import questionary
from questionary import Choice
from rich.console import Console
from rich.panel import Panel

console = Console()


class Menu:
    def __init__(self, title, commands, startup_art=None):
        self.title = title
        self.commands = commands
        self.startup_art = startup_art
        self._startup_shown = False

    def run(self):
        if self.startup_art and not self._startup_shown:
            if callable(self.startup_art):
                self.startup_art()
            else:
                console.print(self.startup_art, style="bold rgb(255,168,0)")
            self._startup_shown = True

        while True:
            choices = [
                Choice(title=f"{key}) {label}", value=key)
                for key, (label, _) in self.commands.items()
            ]

            choice = questionary.select(
                # self.title,
                "",
                choices=choices,
            ).ask()

            if choice is None:  # user hit Ctrl+C
                break

            self.commands[choice][1]()