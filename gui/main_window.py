import sys
import time
from typing import Optional, Dict
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QGroupBox,
    QMessageBox, QSplitter, QStatusBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QAction

from config import Settings
from core import WindowManager, ScreenshotCapture, ActionExecutor, HotkeyManager
from ai.azure_client import AzureOpenAIClient
from data import SessionManager, CSVHandler
from poker import StatsCalculator, HandHistory

from .config_dialog import ConfigDialog
from .stats_panel import StatsPanel
from .log_viewer import LogViewer


class AnalysisWorker(QThread):
    """Worker thread for AI analysis."""

    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(
        self,
        ai_client: AzureOpenAIClient,
        screenshot_base64: str,
        player_stats: Dict,
        hand_history: list,
        game_context: Dict
    ):
        super().__init__()
        self._client = ai_client
        self._screenshot = screenshot_base64
        self._stats = player_stats
        self._history = hand_history
        self._context = game_context

    def run(self):
        try:
            decision = self._client.analyze_with_retry(
                screenshot_base64=self._screenshot,
                player_stats=self._stats,
                hand_history=self._history,
                game_context=self._context
            )
            self.finished.emit(decision)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""

    # Signals for thread-safe hotkey handling
    _hotkey_analysis = pyqtSignal()
    _hotkey_auto_play = pyqtSignal()
    _hotkey_fold = pyqtSignal()
    _hotkey_check = pyqtSignal()
    _hotkey_raise = pyqtSignal()
    _hotkey_stop = pyqtSignal()

    def __init__(self, settings: Settings):
        super().__init__()
        self._settings = settings

        # Initialize components
        self._window_manager = WindowManager()
        self._screenshot = ScreenshotCapture()
        self._actions = ActionExecutor(settings)
        self._hotkey_manager = HotkeyManager()
        self._session_manager = SessionManager()
        self._csv_handler = CSVHandler()
        self._stats_calculator = StatsCalculator()

        # AI client (Azure OpenAI)
        self._ai_client: Optional[AzureOpenAIClient] = None
        self._init_ai_client()

        # State
        self._is_running = False
        self._auto_play = False
        self._player_stats: Dict = {}
        self._current_worker: Optional[AnalysisWorker] = None
        self._windows_list = []

        self._setup_ui()
        self._setup_hotkeys()
        self._setup_timers()
        self._load_player_stats()

    def _init_ai_client(self):
        """Initialize Azure OpenAI client."""
        try:
            azure_key = self._settings.get("ai", "azure_api_key", default="")
            if azure_key:
                self._ai_client = AzureOpenAIClient(self._settings)
            else:
                self._ai_client = None
        except Exception as e:
            self._ai_client = None

    def _setup_ui(self):
        self.setWindowTitle("Poker Bot")
        self.setMinimumSize(900, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top control panel
        control_group = QGroupBox("Controls")
        control_layout = QHBoxLayout(control_group)

        # Window selector
        control_layout.addWidget(QLabel("Window:"))
        self._window_combo = QComboBox()
        self._window_combo.setMinimumWidth(200)
        control_layout.addWidget(self._window_combo)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._refresh_windows)
        control_layout.addWidget(self._refresh_btn)

        control_layout.addStretch()

        # Session controls
        self._start_btn = QPushButton("Start Session")
        self._start_btn.clicked.connect(self._toggle_session)
        control_layout.addWidget(self._start_btn)

        self._config_btn = QPushButton("Configure")
        self._config_btn.clicked.connect(self._open_config)
        control_layout.addWidget(self._config_btn)

        main_layout.addWidget(control_group)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Stats panel (left)
        self._stats_panel = StatsPanel()
        splitter.addWidget(self._stats_panel)

        # Log viewer (right)
        self._log_viewer = LogViewer()
        splitter.addWidget(self._log_viewer)

        splitter.setSizes([400, 500])
        main_layout.addWidget(splitter)

        # Hotkey info panel
        hotkey_group = QGroupBox("Hotkeys")
        hotkey_layout = QHBoxLayout(hotkey_group)

        hotkeys_info = [
            ("F1", "Analyze"),
            ("F2", "Auto-Play"),
            ("F3", "Fold"),
            ("F4", "Check"),
            ("F5", "Raise"),
            ("ESC", "Stop")
        ]

        for key, action in hotkeys_info:
            label = QLabel(f"<b>{key}</b>: {action}")
            hotkey_layout.addWidget(label)
            hotkey_layout.addStretch()

        main_layout.addWidget(hotkey_group)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._update_status("Ready")

        # Menu bar
        self._setup_menu()

        # Initial window list
        self._refresh_windows()

    def _setup_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        export_action = QAction("Export Session", self)
        export_action.triggered.connect(self._export_session)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_hotkeys(self):
        """Setup global hotkeys."""
        # Connect signals to slots (ensures callbacks run on main thread)
        self._hotkey_analysis.connect(self._trigger_analysis)
        self._hotkey_auto_play.connect(self._toggle_auto_play)
        self._hotkey_fold.connect(self._quick_fold)
        self._hotkey_check.connect(self._quick_check)
        self._hotkey_raise.connect(self._quick_raise)
        self._hotkey_stop.connect(self._emergency_stop)

        # Register hotkeys to emit signals (thread-safe)
        self._hotkey_manager.register_hotkey("f1", self._hotkey_analysis.emit)
        self._hotkey_manager.register_hotkey("f2", self._hotkey_auto_play.emit)
        self._hotkey_manager.register_hotkey("f3", self._hotkey_fold.emit)
        self._hotkey_manager.register_hotkey("f4", self._hotkey_check.emit)
        self._hotkey_manager.register_hotkey("f5", self._hotkey_raise.emit)
        self._hotkey_manager.set_emergency_stop(self._hotkey_stop.emit)
        self._hotkey_manager.start()

    def _setup_timers(self):
        """Setup periodic timers."""
        # Update stats display periodically
        self._stats_timer = QTimer()
        self._stats_timer.timeout.connect(self._update_stats_display)
        self._stats_timer.start(5000)  # Every 5 seconds

    def _load_player_stats(self):
        """Load player statistics from CSV."""
        self._player_stats = self._csv_handler.load_player_stats()
        self._stats_panel.update_player_stats(self._player_stats)

    def _refresh_windows(self):
        """Refresh the window list."""
        self._window_combo.clear()
        self._windows_list = self._window_manager.enumerate_windows()

        # Add windows to combo box with stored window objects
        for window in self._windows_list:
            if window.title.strip():
                self._window_combo.addItem(window.title, window)

        # Try to select poker-related window
        for i in range(self._window_combo.count()):
            title = self._window_combo.itemText(i).lower()
            if "ggpoker" in title or "nlh" in title or "plo" in title or "natural8" in title:
                self._window_combo.setCurrentIndex(i)
                break

    def _toggle_session(self):
        """Start or stop a session."""
        if self._is_running:
            self._stop_session()
        else:
            self._start_session()

    def _start_session(self):
        """Start a new session."""
        # Check for AI client
        if not self._ai_client:
            QMessageBox.warning(
                self,
                "No API Key",
                "Azure OpenAI API key not configured."
            )
            return

        # Get selected window directly from combo box data
        window = self._window_combo.currentData()
        window_title = self._window_combo.currentText()

        if not window:
            QMessageBox.warning(self, "No Window", "Please select a window and click Refresh first.")
            return

        # Verify window still exists
        if not self._window_manager._user32.IsWindow(window.handle):
            QMessageBox.warning(self, "Window Closed", "The selected window no longer exists. Please Refresh.")
            return

        self._window_manager.set_current_window(window)

        # Start session
        self._session_manager.start_session()
        self._is_running = True

        self._start_btn.setText("Stop Session")
        self._update_status("Session active")
        self._log_viewer.log_success(f"Session started - tracking: {window_title}")

    def _stop_session(self):
        """Stop the current session."""
        self._is_running = False
        self._auto_play = False

        session = self._session_manager.end_session()
        if session:
            summary = self._session_manager.get_session_summary()
            self._log_viewer.log_success(
                f"Session ended - Hands: {session.hands_played}, "
                f"Profit: {session.profit_bb:+.1f} BB"
            )

        # Save player stats
        self._csv_handler.save_player_stats(self._player_stats)

        self._start_btn.setText("Start Session")
        self._update_status("Session stopped")

    def _trigger_analysis(self):
        """Trigger AI analysis of current game state."""
        if not self._is_running:
            self._log_viewer.log_warning("Session not active")
            return

        if self._current_worker and self._current_worker.isRunning():
            self._log_viewer.log_warning("Analysis already in progress")
            return

        window = self._window_manager.current_window
        if not window or not self._window_manager.is_window_valid():
            self._log_viewer.log_error("Poker window not available")
            return

        # Refresh window position
        self._window_manager.refresh_current_window()
        window = self._window_manager.current_window

        # Debug: log window info
        self._log_viewer.log(f"Target: '{window.title}'")
        self._log_viewer.log(f"Position: {window.x},{window.y} Size: {window.width}x{window.height}")

        # Hide THIS window (bot) completely so it doesn't block the poker window
        self.hide()
        QApplication.processEvents()  # Force UI update
        time.sleep(0.5)

        # Bring poker window to front
        self._window_manager.bring_to_front()
        QApplication.processEvents()
        time.sleep(0.5)

        # Refresh window position
        self._window_manager.refresh_current_window()
        window = self._window_manager.current_window

        # Capture screenshot
        image = self._screenshot.capture_window(window)

        # Restore bot window
        self.show()
        self.activateWindow()
        QApplication.processEvents()

        self._log_viewer.log("Screenshot captured")

        # Debug: save screenshot to file
        debug_path = "./debug_screenshot.png"
        image.save(debug_path)
        self._log_viewer.log(f"Debug screenshot saved to {debug_path}")

        screenshot_b64 = self._screenshot.image_to_base64(image)

        # Get hand history
        history = []
        if self._session_manager.hand_history:
            history = self._session_manager.hand_history.get_summaries_for_ai()

        # Start analysis in background
        self._current_worker = AnalysisWorker(
            self._ai_client,
            screenshot_b64,
            self._player_stats,
            history,
            {}
        )
        self._current_worker.finished.connect(self._on_analysis_complete)
        self._current_worker.error.connect(self._on_analysis_error)
        self._current_worker.start()

        self._log_viewer.log("Analyzing game state...", "AI")

    def _on_analysis_complete(self, decision):
        """Handle completed analysis."""
        self._current_worker = None

        self._log_viewer.log_ai_decision(
            decision.action,
            decision.amount,
            decision.confidence,
            decision.reasoning
        )

        self._stats_panel.update_ai_decision(decision.to_dict())

        # Auto-execute if auto-play is on
        if self._auto_play and decision.is_valid:
            self._execute_action(decision)

    def _on_analysis_error(self, error_msg: str):
        """Handle analysis error."""
        self._current_worker = None
        self._log_viewer.log_error(f"Analysis failed: {error_msg}")

    def _execute_action(self, decision):
        """Execute a poker action."""
        if not self._is_running:
            return

        success = self._actions.perform_action(decision.action, decision.amount)
        if success:
            self._log_viewer.log_success(f"Executed: {decision.action}")
        else:
            self._log_viewer.log_error(f"Failed to execute: {decision.action}")

    def _toggle_auto_play(self):
        """Toggle auto-play mode."""
        self._auto_play = not self._auto_play
        status = "ON" if self._auto_play else "OFF"
        self._log_viewer.log(f"Auto-play: {status}", "INFO")
        self._update_status(f"Auto-play: {status}")

    def _quick_fold(self):
        """Quick fold action."""
        if self._is_running:
            if self._actions.perform_fold():
                self._log_viewer.log_action("Hero", "fold")

    def _quick_check(self):
        """Quick check/call action."""
        if self._is_running:
            if self._actions.perform_check():
                self._log_viewer.log_action("Hero", "check")

    def _quick_raise(self):
        """Quick raise action with configured amount."""
        if self._is_running:
            raise_amount = self._settings.get("quick_raise_bb", default=2.5)
            if self._actions.perform_raise(raise_amount):
                self._log_viewer.log_action("Hero", f"raise {raise_amount}BB")

    def _emergency_stop(self):
        """Emergency stop all actions."""
        self._auto_play = False
        self._log_viewer.log_warning("Emergency stop activated")
        self._update_status("STOPPED")

    def _update_stats_display(self):
        """Update the stats panel display."""
        if self._is_running:
            summary = self._session_manager.get_session_summary()
            if summary:
                self._stats_panel.update_session_stats(
                    hands=summary.get("hands_played", 0),
                    profit_bb=summary.get("profit_bb", 0),
                    bb_per_100=summary.get("bb_per_100", 0),
                    duration_minutes=summary.get("duration_minutes", 0)
                )

    def _update_status(self, message: str):
        """Update status bar."""
        self._status_bar.showMessage(message)

    def _open_config(self):
        """Open configuration dialog."""
        dialog = ConfigDialog(self._settings, self)
        if dialog.exec():
            self._log_viewer.log_success("Configuration saved")
            # Reinitialize action executor with new settings
            self._actions = ActionExecutor(self._settings)

    def _export_session(self):
        """Export current session data."""
        self._log_viewer.log("Export not yet implemented", "WARNING")

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Poker Bot",
            "AI Poker Bot\n\n"
            "Uses Claude Vision API to analyze poker screenshots\n"
            "and recommend optimal actions.\n\n"
            "Hotkeys:\n"
            "F1 - Trigger analysis\n"
            "F2 - Toggle auto-play\n"
            "F3 - Quick fold\n"
            "F4 - Quick check\n"
            "ESC - Emergency stop"
        )

    def closeEvent(self, event):
        """Handle window close."""
        if self._is_running:
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "A session is active. End session and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

            self._stop_session()

        # Cleanup
        self._hotkey_manager.stop()
        self._screenshot.close()

        event.accept()
