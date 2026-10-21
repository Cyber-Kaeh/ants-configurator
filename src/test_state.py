import json
import os
import tempfile
import threading
import unittest
from src.actions import SaveStateAction, LoadStateAction
from src.models import DisplayConfig, DockConfig, IntegralConfig, VCConfig


class FakeState:
    def __init__(self):
        self.display_config = DisplayConfig()
        self.dock_config = DockConfig()
        self.integral_config = IntegralConfig()
        self.vc_config = VCConfig()


class TestSaveLoadState(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp_dir.name, "app_state.json")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _populated_state(self):
        state = FakeState()
        state.display_config.count = 2
        state.display_config.size = "3840x2160"
        state.display_config.serial = "ABC123"
        state.display_config.model = "AvocorG60"
        state.dock_config.add_dock("Dock1", "1920x1080")
        state.dock_config.add_dock("MTR", "1280x720")
        state.integral_config.integrals = {"1": {"serial": "XYZ", "firmware": "1.0"}}
        state.vc_config.multi_display = True
        state.vc_config.placement = 10880
        state.vc_config.teams = True
        return state

    def test_round_trip_keeps_every_field(self):
        before = self._populated_state()
        SaveStateAction(before, self.path).execute()

        after = FakeState()
        LoadStateAction(after, self.path).execute()

        for name in ("display_config", "dock_config", "integral_config", "vc_config"):
            self.assertEqual(getattr(before, name).to_dict(), getattr(after, name).to_dict(), name)

    def test_frame_and_dock_width_are_derived(self):
        state = self._populated_state()
        SaveStateAction(state, self.path).execute()
        loaded = FakeState()
        LoadStateAction(loaded, self.path).execute()

        self.assertEqual(loaded.display_config.placement, 7680)
        self.assertEqual(loaded.display_config.height, 2160)
        # Dock width is only the docks, not the displays in front of them.
        self.assertEqual(loaded.dock_config.total_width, 1920 + 1280)

    def test_frame_is_none_until_count_and_size_set(self):
        display = DisplayConfig()
        self.assertIsNone(display.placement)
        display.size = "1920x1080"
        self.assertIsNone(display.placement)
        display.count = 3
        self.assertEqual(display.placement, 5760)

    def test_invalid_screen_size_rejected(self):
        with self.assertRaises(ValueError):
            DisplayConfig().size = "4k"

    def test_save_leaves_no_temp_file(self):
        SaveStateAction(self._populated_state(), self.path).execute()
        self.assertEqual(os.listdir(self.tmp_dir.name), ["app_state.json"])

    def test_concurrent_saves_produce_valid_json(self):
        state = self._populated_state()
        threads = [threading.Thread(target=SaveStateAction(state, self.path).execute) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        with open(self.path) as f:
            self.assertEqual(json.load(f)["display_config"]["model"], "AvocorG60")

    def test_load_old_format_file(self):
        # Files saved before placement/height were derived still load.
        with open(self.path, "w") as f:
            json.dump({
                "display_config": {"count": 2, "size": "3840x2160", "placement": 7680, "height": 2160, "serial": None},
                "dock_config": {"names": ["Dock1"], "count": 1, "size": ["1920x1080"], "enabled": True},
            }, f)
        state = FakeState()
        LoadStateAction(state, self.path).execute()
        self.assertEqual(state.display_config.placement, 7680)
        self.assertEqual(state.dock_config.total_width, 1920)
        self.assertEqual(state.integral_config.integrals, {})

    def test_load_corrupt_or_null_sections_does_not_raise(self):
        for contents in ("", "{not json", '{"display_config": null}'):
            with open(self.path, "w") as f:
                f.write(contents)
            LoadStateAction(FakeState(), self.path).execute()


if __name__ == "__main__":
    unittest.main()
