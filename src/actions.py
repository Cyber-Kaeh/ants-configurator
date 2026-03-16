import subprocess
import os
import sys
import json
from src.models import DisplayConfig, DockConfig, IntegralConfig, VCConfig


SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts"))
LOCAL_SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "/Local/scripts"))
LOCAL_SERIAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "/Local/scripts/serial"))

STATE_FILE_PATH = os.path.expanduser("~/.config/ants-configurator/app_state.json")

class SaveStateAction:
    def __init__(self, state, file_path=STATE_FILE_PATH):
        self.state = state
        self.file_path = file_path

    def execute(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        data_to_save = {
            "display_config": self.state.display_config.to_dict(),
            "dock_config": self.state.dock_config.to_dict(),
            "integral_config": self.state.integral_config.to_dict(),
            "vc_config": self.state.vc_config.to_dict(),
        }
        with open(self.file_path, "w") as f:
            json.dump(data_to_save, f, indent=4)

class LoadStateAction:
    def __init__(self, state, file_path=STATE_FILE_PATH):
        self.state = state
        self.file_path = file_path

    def execute(self):
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                self.state.display_config = DisplayConfig.from_dict(data.get("display_config", {}))
                self.state.dock_config = DockConfig.from_dict(data.get("dock_config", {}))
                self.state.integral_config = IntegralConfig.from_dict(data.get("integral_config", {}))
                self.state.vc_config = VCConfig.from_dict(data.get("vc_config", {}))
                print("Last configurations loaded.")
        except FileNotFoundError:
            print("No saved configurations found.")
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Error decoding saved configurations: {e}")


class DeleteConfigAction:
    def __init__(self, file_path=STATE_FILE_PATH):
        self.file_path = file_path

    def execute(self):
        try:
            os.remove(self.file_path)
            print("Configuration file deleted.")
        except FileNotFoundError:
            print("No configuration file found.")
        except Exception as e:
            print(f"Error deleting configuration file: {e}")


class ClearConfigAction:
    def __init__(self, state, config_name):
        self.state = state
        self.config_name = config_name
        self.config_map = {
            "display": ("display_config", DisplayConfig),
            "dock": ("dock_config", DockConfig),
            "integral": ("integral_config", IntegralConfig),
            "vc": ("vc_config", VCConfig),
        }

    def execute(self):
        """Resets a specific part of the application state to its default."""
        if self.config_name in self.config_map:
            attr_name, config_class = self.config_map[self.config_name]
            setattr(self.state, attr_name, config_class())
            print(f"{self.config_name.capitalize()} configuration has been cleared.")
            SaveStateAction(self.state).execute()
        else:
            print(f"Error: Unknown configuration '{self.config_name}'")

class ToggleTTMenuAction:  
    def execute(self):
        """Finds and signals the menumonitord or MenuMonitor process."""
        import signal  # Import here to keep it local to this action
        process_names = ['menumonitord', 'MenuMonitor']
        
        for name in process_names:
            try:
                result = subprocess.run(['pgrep', '-f', name], capture_output=True, text=True, check=False)
                if result.returncode == 0 and result.stdout.strip():
                    pid = int(result.stdout.strip().split('\n')[0])
                    print(f"Found {name} with PID {pid}. Sending signal...")
                    os.kill(pid, signal.SIGUSR1)
                    return
            except (subprocess.SubprocessError, ValueError, PermissionError) as e:
                print(f"An error occurred while trying to signal {name}: {e}")
        print("Warning: Could not find menumonitord or MenuMonitor process.")


class WriteDefaultsAction:
    def __init__(self, domain, key, value, value_type=None):
        self.domain = domain
        self.key = key
        self.value = value or []
        self.value_type = value_type

    def execute(self):
        full_domain = f"com.t1visions.{self.domain}"
        command = ["defaults", "write", full_domain, self.key]
        if self.value_type:
            command.append(self.value_type)
        
        if isinstance(self.value, list):
            command.extend(self.value)
        else:
            command.append(str(self.value))
        
        print(f"Running command: {' '.join(map(str, command))}")
        subprocess.run(command, check=True)


class RunCommandAction:
    def __init__(self, command, success_message="Command executed successfully."):
        self.command = command
        self.success_message = success_message

    def execute(self):
        """Executes a generic shell command. Commands are built using a list."""
        try:
            print(f"Running command: {' '.join(self.command)}")
            result = subprocess.run(self.command, check=True, capture_output=True, text=True)
            print(self.success_message)
            if result.stdout:
                print(result.stdout)
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Error running command: {e}")


class AddCrontabEntryAction:
    def __init__(self, command, comment=""):
        if command.startswith("@reboot "):
            self.command = command[len("@reboot "):]
            self.reboot = True
        else:
            self.command = command
            self.reboot = False
        self.comment = comment

    def execute(self):
        from crontab import CronTab
        cron = CronTab(user=True)

        if any(job.command == self.command for job in cron):
            print(f"Crontab entry already exists: '{self.command[:60]}'")
            return

        job = cron.new(command=self.command)
        if self.reboot:
            job.every_reboot()
        if self.comment:
            job.set_comment(self.comment)

        cron.write()
        print(f"Added crontab entry: '{self.command[:60]}'")

class RunIntegralSerialAction:
    def __init__(self, serial, command):
        self.serial = serial
        self.command = command

    def execute(self):
        script_path = os.path.join(LOCAL_SERIAL_DIR, "integralSerial.py")
        result = subprocess.run(
            [sys.executable, script_path, f"/dev/tty.usbserial-{self.serial}", self.command],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"{self.command} command sent successfully.")
            print(result.stdout)
        else:
            print(f"Error: {self.command} command failed with return code {result.returncode}")
            print("Error Output:")
            print(result.stderr)


class RunScriptAction:
    def __init__(self, script_dir, script_name, *args):
        self.script_path = os.path.join(script_dir, script_name)
        self.args = list(args)

    def execute(self):
        command = [self.script_path] + self.args
        try:
            print(f"Running script: {' '.join(command)}")
            subprocess.run(command, check=True)
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"Error running script: {e}")
