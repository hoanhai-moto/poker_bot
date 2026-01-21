from typing import Dict, Optional, Callable
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QGridLayout, QLineEdit,
    QSpinBox, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
import pyautogui
import time


from config import Settings


class MouseCaptureThread(QThread):
    """Thread to capture mouse click position."""

    position_captured = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        """Wait for mouse click and emit position."""
        import ctypes

        # Wait a moment for user to move to target
        time.sleep(0.3)

        # Poll for left mouse button click
        while self._running:
            # Check if left mouse button is pressed (Windows API)
            if ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
                # Get current mouse position
                x, y = pyautogui.position()
                self.position_captured.emit(x, y)
                break
            time.sleep(0.01)

    def stop(self):
        self._running = False


class ConfigDialog(QDialog):
    """Dialog for configuring button positions and settings."""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._capturing = False
        self._capture_button: Optional[str] = None
        self._capture_thread: Optional[MouseCaptureThread] = None

        self.setWindowTitle("Configuration")
        self.setMinimumWidth(400)
        self._setup_ui()
        self._load_current_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Button positions group
        buttons_group = QGroupBox("Button Positions")
        buttons_layout = QGridLayout(buttons_group)

        self._button_inputs: Dict[str, Dict] = {}
        button_names = ["fold", "check", "call", "raise", "bet_input"]

        for i, name in enumerate(button_names):
            label = QLabel(f"{name.replace('_', ' ').title()}:")
            x_input = QSpinBox()
            x_input.setRange(0, 9999)
            x_input.setPrefix("X: ")
            y_input = QSpinBox()
            y_input.setRange(0, 9999)
            y_input.setPrefix("Y: ")
            capture_btn = QPushButton("Capture")
            capture_btn.clicked.connect(lambda checked, n=name: self._start_capture(n))
            test_btn = QPushButton("Test")
            test_btn.clicked.connect(lambda checked, n=name: self._test_position(n))

            buttons_layout.addWidget(label, i, 0)
            buttons_layout.addWidget(x_input, i, 1)
            buttons_layout.addWidget(y_input, i, 2)
            buttons_layout.addWidget(capture_btn, i, 3)
            buttons_layout.addWidget(test_btn, i, 4)

            self._button_inputs[name] = {
                "x": x_input,
                "y": y_input,
                "capture": capture_btn,
                "test": test_btn
            }

        layout.addWidget(buttons_group)

        # Timing settings group
        timing_group = QGroupBox("Timing Settings")
        timing_layout = QGridLayout(timing_group)

        timing_layout.addWidget(QLabel("Min Delay (ms):"), 0, 0)
        self._min_delay = QSpinBox()
        self._min_delay.setRange(100, 10000)
        timing_layout.addWidget(self._min_delay, 0, 1)

        timing_layout.addWidget(QLabel("Max Delay (ms):"), 0, 2)
        self._max_delay = QSpinBox()
        self._max_delay.setRange(100, 10000)
        timing_layout.addWidget(self._max_delay, 0, 3)

        timing_layout.addWidget(QLabel("Typing Delay (ms):"), 1, 0)
        self._typing_delay = QSpinBox()
        self._typing_delay.setRange(10, 500)
        timing_layout.addWidget(self._typing_delay, 1, 1)

        layout.addWidget(timing_group)

        # Capture instructions
        self._capture_label = QLabel("")
        self._capture_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        self._capture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._capture_label)

        # Dialog buttons
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _load_current_settings(self):
        """Load current settings into the UI."""
        for name, inputs in self._button_inputs.items():
            pos = self._settings.get_button_position(name)
            inputs["x"].setValue(pos[0])
            inputs["y"].setValue(pos[1])

        self._min_delay.setValue(self._settings.min_delay_ms)
        self._max_delay.setValue(self._settings.max_delay_ms)
        self._typing_delay.setValue(self._settings.typing_delay_ms)

    def _start_capture(self, button_name: str):
        """Start capturing mouse position for a button."""
        self._capturing = True
        self._capture_button = button_name

        self._capture_label.setText(
            f"Click anywhere to set {button_name.replace('_', ' ')} position...\n"
            "(Press Escape to cancel)"
        )

        # Disable all capture buttons
        for inputs in self._button_inputs.values():
            inputs["capture"].setEnabled(False)

        # Minimize dialog so user can click on poker window
        self.showMinimized()

        # Start capture thread
        self._capture_thread = MouseCaptureThread()
        self._capture_thread.position_captured.connect(self._on_position_captured)
        self._capture_thread.start()

    def _on_position_captured(self, x: int, y: int):
        """Handle captured mouse position."""
        self._capturing = False

        # Restore dialog
        self.showNormal()
        self.activateWindow()

        # Set the position
        self._set_captured_position(x, y)

    def _set_captured_position(self, x: int, y: int):
        """Set the captured position in the UI."""
        if self._capture_button and self._capture_button in self._button_inputs:
            inputs = self._button_inputs[self._capture_button]
            inputs["x"].setValue(int(x))
            inputs["y"].setValue(int(y))

        self._capture_label.setText(f"Position captured: ({x}, {y})")
        self._capture_button = None

        # Re-enable all capture buttons
        for inputs in self._button_inputs.values():
            inputs["capture"].setEnabled(True)

    def _test_position(self, button_name: str):
        """Test a button position by moving the mouse there."""
        try:
            import pyautogui

            inputs = self._button_inputs[button_name]
            x = inputs["x"].value()
            y = inputs["y"].value()

            if x == 0 and y == 0:
                QMessageBox.warning(
                    self,
                    "No Position",
                    f"No position set for {button_name}. Please capture or enter coordinates."
                )
                return

            # Move mouse to position (without clicking)
            pyautogui.moveTo(x, y, duration=0.3)
            self._capture_label.setText(f"Mouse moved to {button_name} position: ({x}, {y})")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to test position: {e}")

    def _save_settings(self):
        """Save settings and close dialog."""
        # Save button positions
        for name, inputs in self._button_inputs.items():
            x = inputs["x"].value()
            y = inputs["y"].value()
            self._settings.set_button_position(name, x, y)

        # Save timing settings
        self._settings.set("timing", "min_delay_ms", value=self._min_delay.value())
        self._settings.set("timing", "max_delay_ms", value=self._max_delay.value())
        self._settings.set("timing", "typing_delay_ms", value=self._typing_delay.value())

        # Save to file
        self._settings.save()

        # Show confirmation
        QMessageBox.information(
            self,
            "Settings Saved",
            "Button positions and settings have been saved to user_config.json"
        )

        self.accept()

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            if self._capturing:
                # Cancel capture
                self._capturing = False
                if self._capture_thread:
                    self._capture_thread.stop()
                    self._capture_thread = None
                self._capture_label.setText("Capture cancelled")
                self._capture_button = None

                # Re-enable all capture buttons
                for inputs in self._button_inputs.values():
                    inputs["capture"].setEnabled(True)
            else:
                self.reject()
        else:
            super().keyPressEvent(event)
