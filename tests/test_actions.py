"""Tests for action execution and automation."""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestActionExecutor(unittest.TestCase):
    """Test action execution functionality."""

    def setUp(self):
        # Mock settings
        self.mock_settings = Mock()
        self.mock_settings.min_delay_ms = 100
        self.mock_settings.max_delay_ms = 200
        self.mock_settings.typing_delay_ms = 10
        self.mock_settings.get_button_position = Mock(return_value=(100, 200))

    @patch('core.actions.pyautogui')
    def test_click_action(self, mock_pyautogui):
        """Test click action."""
        from core.actions import ActionExecutor

        executor = ActionExecutor(self.mock_settings)
        executor.click(100, 200, delay=False)

        mock_pyautogui.click.assert_called_once()

    @patch('core.actions.pyautogui')
    def test_perform_fold(self, mock_pyautogui):
        """Test fold action."""
        from core.actions import ActionExecutor

        executor = ActionExecutor(self.mock_settings)
        result = executor.perform_fold()

        self.assertTrue(result)
        mock_pyautogui.click.assert_called()

    @patch('core.actions.pyautogui')
    def test_perform_fold_no_position(self, mock_pyautogui):
        """Test fold action when position not configured."""
        from core.actions import ActionExecutor

        self.mock_settings.get_button_position = Mock(return_value=(0, 0))
        executor = ActionExecutor(self.mock_settings)
        result = executor.perform_fold()

        self.assertFalse(result)

    @patch('core.actions.pyautogui')
    @patch('core.actions.time')
    def test_perform_raise(self, mock_time, mock_pyautogui):
        """Test raise action sequence."""
        from core.actions import ActionExecutor

        mock_time.sleep = Mock()
        executor = ActionExecutor(self.mock_settings)
        result = executor.perform_raise(15.5)

        self.assertTrue(result)
        # Should have multiple clicks (bet input + raise button)
        self.assertGreaterEqual(mock_pyautogui.click.call_count, 2)

    @patch('core.actions.pyautogui')
    def test_perform_action_dispatch(self, mock_pyautogui):
        """Test action dispatch method."""
        from core.actions import ActionExecutor

        executor = ActionExecutor(self.mock_settings)

        # Test each action type
        self.assertTrue(executor.perform_action("fold"))
        self.assertTrue(executor.perform_action("check"))
        self.assertTrue(executor.perform_action("call"))
        self.assertTrue(executor.perform_action("raise", amount=10))
        self.assertFalse(executor.perform_action("raise"))  # No amount
        self.assertFalse(executor.perform_action("invalid"))

    @patch('core.actions.pyautogui')
    def test_clear_field(self, mock_pyautogui):
        """Test clear field action."""
        from core.actions import ActionExecutor

        executor = ActionExecutor(self.mock_settings)
        executor.clear_field()

        mock_pyautogui.hotkey.assert_called_with('ctrl', 'a')
        mock_pyautogui.press.assert_called_with('delete')


class TestHotkeyManager(unittest.TestCase):
    """Test hotkey management."""

    def test_register_hotkey(self):
        """Test registering a hotkey."""
        from core.hotkey_manager import HotkeyManager

        manager = HotkeyManager()
        callback = Mock()

        manager.register_hotkey("f1", callback)

        # Verify it's registered (internal check)
        self.assertIn("f1", manager._callbacks)

    def test_unregister_hotkey(self):
        """Test unregistering a hotkey."""
        from core.hotkey_manager import HotkeyManager

        manager = HotkeyManager()
        callback = Mock()

        manager.register_hotkey("f1", callback)
        manager.unregister_hotkey("f1")

        self.assertNotIn("f1", manager._callbacks)

    def test_clear_all_hotkeys(self):
        """Test clearing all hotkeys."""
        from core.hotkey_manager import HotkeyManager

        manager = HotkeyManager()

        manager.register_hotkey("f1", Mock())
        manager.register_hotkey("f2", Mock())
        manager.clear_all()

        self.assertEqual(len(manager._callbacks), 0)


class TestWindowManager(unittest.TestCase):
    """Test window management (Windows-specific)."""

    @unittest.skipUnless(sys.platform == 'win32', "Windows only")
    def test_enumerate_windows(self):
        """Test window enumeration."""
        from core.window_manager import WindowManager

        manager = WindowManager()
        windows = manager.enumerate_windows()

        # Should find at least some windows
        self.assertIsInstance(windows, list)

    @unittest.skipUnless(sys.platform == 'win32', "Windows only")
    def test_get_window_titles(self):
        """Test getting window titles."""
        from core.window_manager import WindowManager

        manager = WindowManager()
        titles = manager.get_window_titles()

        self.assertIsInstance(titles, list)


if __name__ == "__main__":
    unittest.main()
