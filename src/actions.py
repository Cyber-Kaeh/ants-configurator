import subprocess
import os
import sys
import json
from models import DisplayConfig, DockConfig, IntegralConfig, VCConfig


SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts"))
LOCAL_SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "/Local/scripts"))
LOCAL_SERIAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "/Local/scripts/serial"))

class SaveStateAction:
    def __init__(self, state, file_path="app_state.json"):
        self.state = state
        self.file_path = file_path

    def execute(self):
        data_to_save = {
            "display_config": self.state.display_config.to_dict(),
            "dock_config": self.state.dock_config.to_dict(),
            "integral_config": self.state.integral_config.to_dict(),
            "vc_config": self.state.vc_config.to_dict(),
        }
        with open(self.file_path, "w") as f:
            json.dump(data_to_save, f, indent=4)
        print("Configurations saved.")

class LoadStateAction:
    def __init__(self, state, file_path="app_state.json"):
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
        self.value = value
        self.value_type = value_type

    def execute(self):
        full_domain = f"com.t1visions.{self.domain}"
        command = ["defaults", "write", full_domain, self.key]
        if self.value_type:
            command.append(self.value_type)
        command.append(self.value)
        
        print(f"Running command: {' '.join(command)}")
        subprocess.run(command, check=True)


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
        print(f"Result: {result.stdout}")
        if result.returncode == 0:
            print(f"{self.command} command sent successfully.")
        else:
            print(f"Error: {self.command} command failed with return code {result.returncode}")
            print("Error Output:")
            print(result.stderr)


class RunScriptAction:
    def __init__(self, script_path, args):
        self.script_path = script_path
        self.args = args

    def execute(self):
        subprocess.run([self.script_path] + self.args)
