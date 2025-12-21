class Menu:
    def __init__(self, title, commands, startup_art=None):
        self.title = title
        self.commands = commands
        self.startup_art = startup_art
        self._startup_shown = False

    def display(self):
        print(f"\n{self.title}")
        print("-" * len(self.title))
        for key, (label, _) in self.commands.items():
            print(f"{key}) {label}")

    def run(self):
        if self.startup_art and not self._startup_shown:
            if callable(self.startup_art):
                self.startup_art()
            else:
                print(self.startup_art)
            self._startup_shown = True
        while True:
            self.display()
            choice = input("> ").strip()

            if choice in self.commands:
                action = self.commands[choice][1]
                action()
            else:
                print("Invalid selection")
