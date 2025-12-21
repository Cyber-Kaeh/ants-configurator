class Menu:
    def __init__(self, title, commands):
        self.title = title
        self.commands = commands

    def display(self):
        print(f"\n{self.title}")
        print("-" * len(self.title))
        for key, (label, _) in self.commands.items():
            print(f"{key}) {label}")

    def run(self):
        while True:
            self.display()
            choice = input("> ").strip()

            if choice in self.commands:
                action = self.commands[choice][1]
                action()
            else:
                print("Invalid selection")
