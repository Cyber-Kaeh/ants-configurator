import subprocess


class WriteDefaultsAction:
    def __init__(self, defaults):
        self.defaults = defaults

    def execute(self):
        pass


class RunScriptAction:
    def __init__(self, script_path, args):
        self.script_path = script_path
        self.args = args

    def execute(self):
        subprocess.run([self.script_path] + self.args)

