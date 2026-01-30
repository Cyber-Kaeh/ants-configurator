import unittest
from unittest.mock import patch, MagicMock, call
import subprocess
from actions import AddCrontabEntryAction

class TestAddCrontabEntryAction(unittest.TestCase):

    @patch('subprocess.run')
    def test_execute_with_new_entry(self, mock_subprocess_run):
        """
        Tests that AddCrontabEntryAction correctly calls the shell command for a label
        and then for an entry, simulating adding a commented and an actual crontab entry.
        """
        # Arrange
        label = "#A mock crontab"
        entry = "@reboot /usr/bin/python /path/to/script.py"
        action = AddCrontabEntryAction(entry)
        action2 = AddCrontabEntryAction(label)

        # Configure the mock to simulate a successful run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = "" # Simulate empty crontab initially
        mock_subprocess_run.return_value = mock_result

        # Act
        action.execute()
        action2.execute()

        # Assert
        expected_label_command = f'(crontab -l 2>/dev/null | grep -Fq -- "{label}") || (crontab -l 2>/dev/null; echo "{label}") | crontab -'
        expected_command = f'(crontab -l 2>/dev/null | grep -Fq -- "{entry}") || (crontab -l 2>/dev/null; echo "{entry}") | crontab -'
        
        calls = [
            call(expected_command, shell=True, check=True, capture_output=True, text=True),
            call(expected_label_command, shell=True, check=True, capture_output=True, text=True)
        ]
        
        # Check that subprocess.run was called with both commands.
        # The order doesn't matter for this assertion.
        mock_subprocess_run.assert_has_calls(calls, any_order=True)
        
        # Verify it was called exactly twice.
        self.assertEqual(mock_subprocess_run.call_count, 2)



    @patch('subprocess.run')
    def test_execute_handles_error(self, mock_subprocess_run):
        """
        Tests that AddCrontabEntryAction handles a CalledProcessError from subprocess.
        """
        # Arrange
        entry = "some entry"
        action = AddCrontabEntryAction(entry)
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="some error")

        # Act & Assert
        # We can check that it prints an error message, for example.
        # Here, we'll just confirm it doesn't crash and the mock was called.
        action.execute()
        self.assertTrue(mock_subprocess_run.called)