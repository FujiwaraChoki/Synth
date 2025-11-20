import os
import sys
import json
import g4f
import requests
import markdown2
import qtawesome as qta

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *

class ToggleSwitch(QCheckBox):
    """Custom toggle switch widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 24)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Track
        track_rect = QRectF(0, 0, 50, 24)
        if self.isChecked():
            painter.setBrush(QColor("#5B9CF6"))
        else:
            painter.setBrush(QColor(60, 60, 60, 100))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, 12, 12)

        # Thumb
        thumb_x = 26 if self.isChecked() else 2
        thumb_rect = QRectF(thumb_x, 2, 20, 20)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(thumb_rect)

class ChatSlidePanel(QWidget):
    """Slide-out chat panel from the right side"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.is_open = False
        self.setFixedWidth(480)
        self.setup_ui()

    def setup_ui(self):
        """Setup the chat panel UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("chatHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)

        header_title = QLabel("AI Assistant")
        header_title.setStyleSheet("font-size: 18px; font-weight: 600;")

        close_btn = QPushButton("✕")
        close_btn.setObjectName("chatCloseButton")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.toggle)

        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)

        # Chat display area
        self.chat_output = QTextEdit()
        self.chat_output.setReadOnly(True)
        self.chat_output.setObjectName("chatOutput")

        # Input area
        input_container = QWidget()
        input_container.setObjectName("chatInputContainer")
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(16, 12, 16, 16)
        input_layout.setSpacing(12)

        # Message input
        message_input_layout = QHBoxLayout()

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Type your message...")
        self.input_edit.setObjectName("chatInput")
        self.input_edit.setMinimumHeight(44)
        self.input_edit.returnPressed.connect(self.send_message)

        send_btn = QPushButton("Send")
        send_btn.setObjectName("chatSendButton")
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setFixedSize(80, 44)
        send_btn.clicked.connect(self.send_message)

        message_input_layout.addWidget(self.input_edit)
        message_input_layout.addWidget(send_btn)

        # Clear chat button
        clear_btn = QPushButton("Clear Chat")
        clear_btn.setObjectName("chatClearButton")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setMinimumHeight(36)
        clear_btn.clicked.connect(self.clear_chat)

        input_layout.addLayout(message_input_layout)
        input_layout.addWidget(clear_btn)

        # Add all to main layout
        layout.addWidget(header)
        layout.addWidget(self.chat_output, 1)
        layout.addWidget(input_container)

        # Set object name for styling
        self.setObjectName("chatSlidePanel")

    def toggle(self):
        """Toggle the chat panel visibility"""
        if self.is_open:
            self.close_panel()
        else:
            self.open_panel()

    def open_panel(self):
        """Open the chat panel"""
        self.show()
        self.is_open = True
        # Focus on input
        self.input_edit.setFocus()

    def close_panel(self):
        """Close the chat panel"""
        self.is_open = False
        self.hide()

    def send_message(self):
        """Send message to AI"""
        prompt = self.input_edit.text().strip()
        if not prompt:
            return

        # Add user message
        self.parent_window.chat_history.append({
            "role": "user",
            "content": prompt
        })
        self.apply_styles(prompt, role="user")

        self.input_edit.clear()

        # Generate AI response
        try:
            ai_response = self.parent_window.generate_response(prompt)
            self.parent_window.chat_history.append({
                "role": "assistant",
                "content": ai_response
            })
            self.apply_styles(ai_response, role="assistant")
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.apply_styles(error_msg, role="error")

    def clear_chat(self):
        """Clear chat history"""
        self.parent_window.chat_history.clear()
        self.chat_output.clear()

    def apply_styles(self, message, role):
        """Apply styles to chat messages"""
        # Convert markdown to HTML
        message_html = markdown2.markdown(message)
        accent = getattr(self.parent_window, "accent_color", "#5B9CF6")
        dark = getattr(self.parent_window, "dark_mode", False)

        def hex_to_rgba(hex_color, alpha):
            """Convert #rrggbb to rgba string for inline styling."""
            hex_color = hex_color.lstrip("#")
            if len(hex_color) != 6:
                return f"rgba(91, 156, 246, {alpha})"
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"

        if role == "user":
            bubble_bg = hex_to_rgba(accent, 0.16) if dark else hex_to_rgba(accent, 0.12)
            border = hex_to_rgba(accent, 0.5)
            prefix = "You"
            prefix_color = accent
        elif role == "assistant":
            bubble_bg = "rgba(255, 255, 255, 0.06)" if dark else "rgba(0, 0, 0, 0.04)"
            border = "rgba(255, 255, 255, 0.12)" if dark else "rgba(0, 0, 0, 0.08)"
            prefix = "AI"
            prefix_color = "#3ed599" if dark else "#1f9e5c"
        else:
            bubble_bg = "rgba(255, 83, 112, 0.08)" if dark else "rgba(217, 48, 82, 0.12)"
            border = "rgba(255, 83, 112, 0.45)"
            prefix = "Error"
            prefix_color = "#ff5370"

        text_color = "#e9edf7" if dark else "#0f1629"
        shadow_alpha = 0.18 if dark else 0.08

        self.chat_output.append(
            f"""
            <div style="
                margin: 10px 6px 12px;
                padding: 12px 14px;
                border-radius: 14px;
                background: {bubble_bg};
                border: 1px solid {border};
                box-shadow: 0 10px 32px rgba(0, 0, 0, {shadow_alpha});
            ">
                <div style="font-weight: 700; color: {prefix_color}; margin-bottom: 6px;">
                    {prefix}
                </div>
                <div style="color: {text_color}; line-height: 1.55; font-size: 14px;">
                    {message_html}
                </div>
            </div>
            """
        )

        # Scroll to bottom
        self.chat_output.verticalScrollBar().setValue(
            self.chat_output.verticalScrollBar().maximum()
        )

    def load_history(self):
        """Load chat history into the panel"""
        self.chat_output.clear()
        for message in self.parent_window.chat_history:
            self.apply_styles(message["content"], role=message["role"])

class BrowserTab(QWidget):
    """Individual browser tab widget"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Browser view - fully opaque
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.google.com"))
        self.browser.setStyleSheet("QWebEngineView { background-color: white; border-radius: 8px; }")
        self.layout.addWidget(self.browser)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("loadProgress")
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(4)
        self.progress_bar.setStyleSheet("")
        self.layout.addWidget(self.progress_bar)

        # Connect signals
        self.browser.loadProgress.connect(self.update_progress)
        self.browser.loadFinished.connect(self.load_finished)

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)
        if progress < 100:
            self.progress_bar.show()

    def load_finished(self):
        self.progress_bar.hide()

class Synth(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Synth Browser")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon("assets/icon.png"))

        # Make window translucent for glassmorphic effect
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Theme
        self.dark_mode = False

        # Tab orientation
        self.vertical_tabs = False

        # Accent color from webpage
        self.accent_color = "#5B9CF6"  # Default blue

        # Data storage
        self.bookmarks = self.load_bookmarks()
        self.history_list = []

        # Browser compatibility helpers
        self.configure_web_engine()

        # Setup UI
        self.setup_ui()
        self.apply_theme()

    def configure_web_engine(self):
        """Set modern UA and inject polyfills so newer sites run correctly."""
        profile = QWebEngineProfile.defaultProfile()

        # Some sites block very old Chromium UAs shipped with Qt; spoof a modern one.
        modern_user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        profile.setHttpUserAgent(modern_user_agent)

        # Install JS polyfills once to cover APIs missing in Qt's Chromium build.
        if getattr(self, "_polyfills_installed", False):
            return

        polyfill_script = QWebEngineScript()
        polyfill_script.setName("synth-polyfills")
        polyfill_script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        polyfill_script.setRunsOnSubFrames(True)
        polyfill_script.setWorldId(QWebEngineScript.MainWorld)
        polyfill_script.setSourceCode(
            """
            (() => {
                try {
                    if (typeof window.crypto === 'undefined') {
                        window.crypto = {};
                    }
                    if (window.crypto && typeof window.crypto.randomUUID !== 'function') {
                        const getBytes = (len) => {
                            if (window.crypto && typeof window.crypto.getRandomValues === 'function') {
                                const arr = new Uint8Array(len);
                                window.crypto.getRandomValues(arr);
                                return arr;
                            }
                            const arr = new Uint8Array(len);
                            for (let i = 0; i < len; i += 1) {
                                arr[i] = Math.floor(Math.random() * 256);
                            }
                            return arr;
                        };

                        window.crypto.randomUUID = function randomUUID() {
                            const bytes = getBytes(16);
                            bytes[6] = (bytes[6] & 0x0f) | 0x40;
                            bytes[8] = (bytes[8] & 0x3f) | 0x80;
                            const toHex = Array.from(bytes, (b) => ('0' + b.toString(16)).slice(-2));
                            return [
                                toHex.slice(0, 4).join(''),
                                toHex.slice(4, 6).join(''),
                                toHex.slice(6, 8).join(''),
                                toHex.slice(8, 10).join(''),
                                toHex.slice(10, 16).join('')
                            ].join('-');
                        };
                    }

                    if (!Array.prototype.at) {
                        Array.prototype.at = function at(n) {
                            const len = this.length;
                            const i = Math.trunc(n) || 0;
                            const idx = i < 0 ? len + i : i;
                            if (idx < 0 || idx >= len) return undefined;
                            return this[idx];
                        };
                    }

                    if (!String.prototype.at) {
                        String.prototype.at = function at(n) {
                            const len = this.length;
                            const i = Math.trunc(n) || 0;
                            const idx = i < 0 ? len + i : i;
                            if (idx < 0 || idx >= len) return '';
                            return this.charAt(idx);
                        };
                    }

                    if (!Object.hasOwn) {
                        Object.hasOwn = function hasOwn(obj, prop) {
                            return Object.prototype.hasOwnProperty.call(obj, prop);
                        };
                    }
                } catch (err) {
                    console.warn('Synth compatibility polyfill failed', err);
                }
            })();
            """
        )

        profile.scripts().insert(polyfill_script)
        self._polyfills_installed = True

    def setup_ui(self):
        """Setup the main UI"""
        # Central widget
        central_widget = QWidget()
        central_widget.setObjectName("appRoot")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top navigation bar
        nav_bar = QWidget()
        nav_bar.setObjectName("navBar")
        nav_shadow = QGraphicsDropShadowEffect(self)
        nav_shadow.setBlurRadius(24)
        nav_shadow.setOffset(0, 10)
        nav_shadow.setColor(QColor(0, 0, 0, 45))
        nav_bar.setGraphicsEffect(nav_shadow)
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(10, 10, 10, 10)
        nav_layout.setSpacing(6)

        # Brand block
        brand_wrapper = QWidget()
        brand_layout = QHBoxLayout(brand_wrapper)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(8)

        brand_accent = QFrame()
        brand_accent.setObjectName("brandAccent")
        brand_accent.setFixedSize(12, 12)

        brand_label = QLabel("Synth")
        brand_label.setObjectName("brandLabel")
        brand_label.setFixedHeight(24)

        brand_layout.addWidget(brand_accent)
        brand_layout.addWidget(brand_label)
        brand_layout.setAlignment(Qt.AlignVCenter)
        nav_layout.addWidget(brand_wrapper)

        # Navigation buttons
        self.back_btn = self.create_icon_button("fa5s.arrow-left", "Go back")
        self.forward_btn = self.create_icon_button("fa5s.arrow-right", "Go forward")
        self.refresh_btn = self.create_icon_button("fa5s.sync-alt", "Refresh page")
        self.home_btn = self.create_icon_button("fa5s.home", "Home")
        self.stop_btn = self.create_icon_button("fa5s.stop-circle", "Stop loading")

        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search...")
        self.url_bar.setObjectName("urlBar")
        self.url_bar.returnPressed.connect(self.navigate_to_url)

        # Action buttons
        self.bookmark_btn = self.create_icon_button("fa5s.star", "Add bookmark")
        self.bookmarks_btn = self.create_icon_button("fa5s.book", "View bookmarks")
        self.history_btn = self.create_icon_button("fa5s.history", "View history")
        self.zoom_out_btn = self.create_icon_button("fa5s.search-minus", "Zoom out")
        self.zoom_reset_btn = self.create_nav_button("100%", "Reset zoom")
        self.zoom_in_btn = self.create_icon_button("fa5s.search-plus", "Zoom in")
        self.ai_chat_btn = self.create_icon_button("fa5s.comments", "Chat with AI")
        self.ai_image_btn = self.create_icon_button("fa5s.image", "Generate Image")
        self.settings_btn = self.create_icon_button("fa5s.cog", "Settings")

        # Add widgets to nav layout
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.forward_btn)
        nav_layout.addWidget(self.refresh_btn)
        nav_layout.addWidget(self.home_btn)
        nav_layout.addWidget(self.stop_btn)
        nav_layout.addWidget(self.url_bar)
        nav_layout.addWidget(self.bookmark_btn)
        nav_layout.addWidget(self.bookmarks_btn)
        nav_layout.addWidget(self.history_btn)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        nav_layout.addWidget(separator)

        nav_layout.addWidget(self.zoom_out_btn)
        nav_layout.addWidget(self.zoom_reset_btn)
        nav_layout.addWidget(self.zoom_in_btn)

        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        nav_layout.addWidget(separator2)

        nav_layout.addWidget(self.ai_chat_btn)
        nav_layout.addWidget(self.ai_image_btn)
        nav_layout.addWidget(self.settings_btn)

        # Content area with horizontal layout for tabs and chat panel
        content_widget = QWidget()
        content_widget.setObjectName("contentArea")
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setObjectName("tabWidget")
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.current_tab_changed)

        # Center align tab text
        self.tabs.tabBar().setExpanding(False)

        # New tab button
        self.tabs.setCornerWidget(self.create_new_tab_button(), Qt.TopRightCorner)

        # Add tabs to content layout
        content_layout.addWidget(self.tabs)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Add layouts
        main_layout.addWidget(nav_bar)
        main_layout.addWidget(content_widget)

        # Connect signals
        self.back_btn.clicked.connect(self.navigate_back)
        self.forward_btn.clicked.connect(self.navigate_forward)
        self.refresh_btn.clicked.connect(self.refresh_page)
        self.home_btn.clicked.connect(self.navigate_home)
        self.stop_btn.clicked.connect(self.stop_loading)
        self.bookmark_btn.clicked.connect(self.add_bookmark)
        self.bookmarks_btn.clicked.connect(self.show_bookmarks)
        self.history_btn.clicked.connect(self.show_history)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_reset_btn.clicked.connect(self.zoom_reset)
        self.ai_chat_btn.clicked.connect(self.open_chat_window)
        self.ai_image_btn.clicked.connect(self.open_image_window)
        self.settings_btn.clicked.connect(self.open_settings)

        # Chat history
        self.chat_history = []

        # Initialize g4f client for AI chat
        self.g4f_client = g4f.Client()

        # Keyboard shortcuts
        self.setup_shortcuts()

        # Create chat slide panel and add to content layout
        self.chat_panel = ChatSlidePanel(self)
        self.chat_panel.hide()
        content_layout.addWidget(self.chat_panel)

        # Create initial tab
        self.add_new_tab()

    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Meta+Tab to open new tab (Command+Tab on macOS, Win+Tab on others)
        new_tab_shortcut = QShortcut(QKeySequence("Meta+Tab"), self)
        new_tab_shortcut.activated.connect(self.add_new_tab)

        # Also add Ctrl+T as a standard shortcut for new tab
        new_tab_shortcut2 = QShortcut(QKeySequence.AddTab, self)
        new_tab_shortcut2.activated.connect(self.add_new_tab)

        # Ctrl+W to close tab
        close_tab_shortcut = QShortcut(QKeySequence.Close, self)
        close_tab_shortcut.activated.connect(lambda: self.close_tab(self.tabs.currentIndex()))

        # Ctrl+L to focus URL bar
        focus_url_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        focus_url_shortcut.activated.connect(lambda: self.url_bar.setFocus())

        # F5 to refresh
        refresh_shortcut = QShortcut(QKeySequence.Refresh, self)
        refresh_shortcut.activated.connect(self.refresh_page)

        # Meta+, to open settings
        settings_shortcut = QShortcut(QKeySequence("Meta+,"), self)
        settings_shortcut.activated.connect(self.open_settings)

        # Option+A (Mac) / Alt+A (Windows) to toggle AI chat panel
        toggle_chat_shortcut = QShortcut(QKeySequence("Alt+A"), self)
        toggle_chat_shortcut.activated.connect(self.toggle_chat_panel)

    def create_icon_button(self, icon_name, tooltip):
        """Create a navigation button with icon"""
        btn = QPushButton()
        btn.setIcon(qta.icon(icon_name))
        btn.setIconSize(QSize(18, 18))
        btn.setToolTip(tooltip)
        btn.setObjectName("navButton")
        btn.setFixedSize(34, 34)
        btn.setCursor(Qt.PointingHandCursor)
        return btn

    def create_nav_button(self, text, tooltip):
        """Create a navigation button with text"""
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setObjectName("navButton")
        btn.setFixedSize(36, 36)
        btn.setCursor(Qt.PointingHandCursor)
        return btn

    def create_new_tab_button(self):
        """Create new tab button"""
        btn = QPushButton("+")
        btn.setToolTip("New tab")
        btn.setFixedSize(30, 30)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda checked=False: self.add_new_tab())
        btn.setObjectName("newTabButton")
        return btn

    def add_new_tab(self, url="https://www.google.com", label="New Tab"):
        """Add a new browser tab"""
        if isinstance(url, bool) or not url:
            url = "https://www.google.com"

        browser_tab = BrowserTab(self)

        # Connect signals
        browser_tab.browser.urlChanged.connect(
            lambda qurl, browser_tab=browser_tab: self.update_url(qurl, browser_tab)
        )
        browser_tab.browser.titleChanged.connect(
            lambda title, browser_tab=browser_tab: self.update_title(title, browser_tab)
        )
        browser_tab.browser.loadStarted.connect(self.load_started)
        browser_tab.browser.loadFinished.connect(self.load_finished)

        # Add tab
        i = self.tabs.addTab(browser_tab, label)
        self.tabs.setCurrentIndex(i)

        # Navigate to URL
        if url != "https://www.google.com":
            browser_tab.browser.setUrl(QUrl(url))

        return browser_tab

    def close_tab(self, i):
        """Close a tab"""
        if self.tabs.count() > 1:
            self.tabs.removeTab(i)
        else:
            self.close()

    def current_tab_changed(self, i):
        """Handle tab change"""
        if i >= 0:
            browser_tab = self.tabs.currentWidget()
            if browser_tab:
                url = browser_tab.browser.url().toString()
                self.url_bar.setText(url)
                self.update_navigation_buttons()

    def update_url(self, qurl, browser_tab=None):
        """Update URL bar"""
        if browser_tab == self.tabs.currentWidget():
            url = qurl.toString()
            self.url_bar.setText(url)
            self.update_navigation_buttons()

            # Add to history
            if url and url not in ["about:blank", ""]:
                title = browser_tab.browser.title() if browser_tab else "Untitled"
                self.add_to_history(url, title)

    def update_title(self, title, browser_tab=None):
        """Update tab title"""
        index = self.tabs.indexOf(browser_tab)
        if index >= 0:
            # Limit title length
            display_title = title[:20] + "..." if len(title) > 20 else title
            self.tabs.setTabText(index, display_title or "New Tab")

    def update_navigation_buttons(self):
        """Update navigation button states"""
        browser_tab = self.tabs.currentWidget()
        if browser_tab:
            self.back_btn.setEnabled(browser_tab.browser.history().canGoBack())
            self.forward_btn.setEnabled(browser_tab.browser.history().canGoForward())

    def load_started(self):
        """Handle page load start"""
        self.status.showMessage("Loading...")

    def load_finished(self):
        """Handle page load finish"""
        self.status.showMessage("Ready", 2000)
        self.update_navigation_buttons()

        # Extract dominant color from webpage
        self.extract_webpage_color()

    def navigate_to_url(self):
        """Navigate to URL from URL bar"""
        url = self.url_bar.text().strip()
        if not url:
            return

        # Check if it's a search query or URL
        if " " in url or ("." not in url and "localhost" not in url):
            # Search query
            url = f"https://www.google.com/search?q={url}"
        elif not url.startswith("http"):
            url = "https://" + url

        browser_tab = self.tabs.currentWidget()
        if browser_tab:
            browser_tab.browser.setUrl(QUrl(url))

    def navigate_back(self):
        """Navigate back"""
        browser_tab = self.tabs.currentWidget()
        if browser_tab:
            browser_tab.browser.back()

    def navigate_forward(self):
        """Navigate forward"""
        browser_tab = self.tabs.currentWidget()
        if browser_tab:
            browser_tab.browser.forward()

    def refresh_page(self):
        """Refresh current page"""
        browser_tab = self.tabs.currentWidget()
        if browser_tab:
            browser_tab.browser.reload()

    def navigate_home(self):
        """Navigate to home page"""
        browser_tab = self.tabs.currentWidget()
        if browser_tab:
            browser_tab.browser.setUrl(QUrl("https://www.google.com"))

    def stop_loading(self):
        """Stop loading page"""
        browser_tab = self.tabs.currentWidget()
        if browser_tab:
            browser_tab.browser.stop()

    # Zoom functions
    def zoom_in(self):
        """Zoom in"""
        browser_tab = self.tabs.currentWidget()
        if browser_tab:
            current_zoom = browser_tab.browser.zoomFactor()
            browser_tab.browser.setZoomFactor(current_zoom + 0.1)
            self.update_zoom_label()

    def zoom_out(self):
        """Zoom out"""
        browser_tab = self.tabs.currentWidget()
        if browser_tab:
            current_zoom = browser_tab.browser.zoomFactor()
            browser_tab.browser.setZoomFactor(max(0.25, current_zoom - 0.1))
            self.update_zoom_label()

    def zoom_reset(self):
        """Reset zoom"""
        browser_tab = self.tabs.currentWidget()
        if browser_tab:
            browser_tab.browser.setZoomFactor(1.0)
            self.update_zoom_label()

    def update_zoom_label(self):
        """Update zoom label"""
        browser_tab = self.tabs.currentWidget()
        if browser_tab:
            zoom = int(browser_tab.browser.zoomFactor() * 100)
            self.zoom_reset_btn.setText(f"{zoom}%")

    def extract_webpage_color(self):
        """Extract dominant color from current webpage"""
        browser_tab = self.tabs.currentWidget()
        if not browser_tab:
            return

        # Get the favicon color or use default
        # This is a simplified approach - we'll use the URL to determine color
        url = browser_tab.browser.url().toString()

        # Use JavaScript to get the theme color from the webpage
        browser_tab.browser.page().runJavaScript("""
            (function() {
                var metaThemeColor = document.querySelector('meta[name="theme-color"]');
                if (metaThemeColor) {
                    return metaThemeColor.getAttribute('content');
                }
                return null;
            })();
        """, self.update_accent_color)

    def update_accent_color(self, color):
        """Update the accent color based on webpage"""
        if color and color.startswith('#'):
            self.accent_color = color
        elif color and color.startswith('rgb'):
            # Convert rgb to hex
            try:
                rgb_values = color.replace('rgb(', '').replace('rgba(', '').replace(')', '').split(',')[:3]
                r, g, b = [int(v.strip()) for v in rgb_values]
                self.accent_color = f"#{r:02x}{g:02x}{b:02x}"
            except:
                self.accent_color = "#5B9CF6"
        else:
            self.accent_color = "#5B9CF6"

        # Reapply theme with new accent color
        self.apply_theme()

    # Bookmarks
    def load_bookmarks(self):
        """Load bookmarks from file"""
        try:
            if os.path.exists("bookmarks.json"):
                with open("bookmarks.json", "r") as f:
                    return json.load(f)
        except:
            pass
        return []

    def save_bookmarks(self):
        """Save bookmarks to file"""
        try:
            with open("bookmarks.json", "w") as f:
                json.dump(self.bookmarks, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save bookmarks: {str(e)}")

    def add_bookmark(self):
        """Add current page to bookmarks"""
        browser_tab = self.tabs.currentWidget()
        if browser_tab:
            url = browser_tab.browser.url().toString()
            title = browser_tab.browser.title()

            # Check if already bookmarked
            if any(b["url"] == url for b in self.bookmarks):
                QMessageBox.information(self, "Bookmark", "This page is already bookmarked!")
                return

            self.bookmarks.append({"title": title, "url": url})
            self.save_bookmarks()
            QMessageBox.information(self, "Bookmark", "Page added to bookmarks!")

    def show_bookmarks(self):
        """Show bookmarks dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Bookmarks")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)

        # Bookmarks list
        list_widget = QListWidget()
        list_widget.setObjectName("bookmarksList")

        for bookmark in self.bookmarks:
            item = QListWidgetItem(f"{bookmark['title']}\n{bookmark['url']}")
            item.setData(Qt.UserRole, bookmark['url'])
            list_widget.addItem(item)

        list_widget.itemDoubleClicked.connect(
            lambda item: self.open_bookmark(item.data(Qt.UserRole), dialog)
        )

        layout.addWidget(list_widget)

        # Buttons
        btn_layout = QHBoxLayout()

        open_btn = QPushButton("Open")
        open_btn.clicked.connect(
            lambda: self.open_bookmark(
                list_widget.currentItem().data(Qt.UserRole) if list_widget.currentItem() else None,
                dialog
            )
        )

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(
            lambda: self.delete_bookmark(list_widget)
        )

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)

        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        dialog.exec_()

    def open_bookmark(self, url, dialog):
        """Open a bookmark"""
        if url:
            self.add_new_tab(url=url, label="Loading...")
            dialog.close()

    def delete_bookmark(self, list_widget):
        """Delete a bookmark"""
        current_item = list_widget.currentItem()
        if current_item:
            url = current_item.data(Qt.UserRole)
            self.bookmarks = [b for b in self.bookmarks if b['url'] != url]
            self.save_bookmarks()
            list_widget.takeItem(list_widget.row(current_item))

    # History
    def add_to_history(self, url, title):
        """Add to history"""
        self.history_list.append({
            "title": title,
            "url": url,
            "time": QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        })

    def show_history(self):
        """Show history dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("History")
        dialog.setMinimumSize(700, 500)

        layout = QVBoxLayout(dialog)

        # History list
        list_widget = QListWidget()
        list_widget.setObjectName("historyList")

        for entry in reversed(self.history_list[-100:]):  # Show last 100 entries
            item = QListWidgetItem(
                f"{entry['time']}\n{entry['title']}\n{entry['url']}"
            )
            item.setData(Qt.UserRole, entry['url'])
            list_widget.addItem(item)

        list_widget.itemDoubleClicked.connect(
            lambda item: self.open_history_item(item.data(Qt.UserRole), dialog)
        )

        layout.addWidget(list_widget)

        # Buttons
        btn_layout = QHBoxLayout()

        open_btn = QPushButton("Open")
        open_btn.clicked.connect(
            lambda: self.open_history_item(
                list_widget.currentItem().data(Qt.UserRole) if list_widget.currentItem() else None,
                dialog
            )
        )

        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(
            lambda: self.clear_history(list_widget)
        )

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)

        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        dialog.exec_()

    def open_history_item(self, url, dialog):
        """Open a history item"""
        if url:
            self.add_new_tab(url=url, label="Loading...")
            dialog.close()

    def clear_history(self, list_widget):
        """Clear history"""
        reply = QMessageBox.question(
            self, "Clear History",
            "Are you sure you want to clear all history?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.history_list.clear()
            list_widget.clear()

    # AI Features
    def open_chat_window(self):
        """Toggle AI chat panel"""
        self.toggle_chat_panel()

    def toggle_chat_panel(self):
        """Toggle the AI chat slide panel"""
        # Load history into panel before opening
        if not self.chat_panel.is_open:
            self.chat_panel.load_history()
        self.chat_panel.toggle()

    def generate_response(self, prompt):
        """Generate AI response using latest g4f models"""
        try:
            # Try with GPT-4 (best quality)
            response = self.g4f_client.chat.completions.create(
                model="gpt-4",  # Latest models available: gpt-4, gpt-4-turbo, claude-3-opus, gemini-pro
                messages=self.chat_history,
            )
            return response.choices[0].message.content
        except Exception as e:
            # Fallback to GPT-3.5-turbo if GPT-4 fails
            try:
                response = self.g4f_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=self.chat_history,
                )
                return response.choices[0].message.content
            except Exception as fallback_error:
                raise Exception(f"AI service unavailable. Primary error: {str(e)}, Fallback error: {str(fallback_error)}")

    def open_image_window(self):
        """Open AI image generation window"""
        image_dialog = QDialog(self)
        image_dialog.setWindowTitle("🎨 AI Image Generator")
        image_dialog.setMinimumSize(600, 700)
        image_dialog.setObjectName("aiDialog")

        layout = QVBoxLayout(image_dialog)

        # Title
        title = QLabel("Generate images with AI")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Input area
        input_layout = QHBoxLayout()

        input_edit = QLineEdit()
        input_edit.setPlaceholderText("Describe the image you want to generate...")
        input_edit.setObjectName("chatInput")
        input_edit.setMinimumHeight(40)

        generate_btn = QPushButton("Generate")
        generate_btn.setObjectName("sendButton")
        generate_btn.setCursor(Qt.PointingHandCursor)
        generate_btn.setMinimumHeight(40)

        input_layout.addWidget(input_edit)
        input_layout.addWidget(generate_btn)

        layout.addLayout(input_layout)

        # Image display
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("imageScrollArea")

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumSize(400, 400)

        # Load placeholder or previous image
        if os.path.exists("assets/temp_img.png"):
            pixmap = QPixmap("assets/temp_img.png")
        else:
            pixmap = QPixmap("assets/placeholder.jpg")

        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                500, 500,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            image_label.setPixmap(scaled_pixmap)

        scroll_area.setWidget(image_label)
        layout.addWidget(scroll_area)

        # Status label
        status_label = QLabel("Ready to generate")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(status_label)

        # Connect generate button
        generate_btn.clicked.connect(
            lambda: self.generate_image(input_edit, image_label, status_label)
        )
        input_edit.returnPressed.connect(
            lambda: self.generate_image(input_edit, image_label, status_label)
        )

        image_dialog.exec_()

    def generate_image(self, input_edit, image_label, status_label):
        """Generate AI image"""
        prompt = input_edit.text().strip()
        if not prompt:
            return

        status_label.setText("Generating image... Please wait.")
        status_label.setStyleSheet("color: #2196F3; margin: 10px;")
        QApplication.processEvents()

        try:
            url = "https://hercai.onrender.com/prodia/text2image?prompt=" + prompt
            response = requests.get(url, timeout=30)
            image_url = response.json()["url"]

            # Save image
            with open("assets/temp_img.png", "wb") as f:
                f.write(requests.get(image_url).content)

            # Display image
            pixmap = QPixmap("assets/temp_img.png")
            scaled_pixmap = pixmap.scaled(
                500, 500,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            image_label.setPixmap(scaled_pixmap)

            status_label.setText("Image generated successfully!")
            status_label.setStyleSheet("color: #4CAF50; margin: 10px;")
        except Exception as e:
            status_label.setText(f"Error: {str(e)}")
            status_label.setStyleSheet("color: #f44336; margin: 10px;")

    # Settings
    def open_settings(self):
        """Open settings dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("⚙️ Settings")
        dialog.setMinimumSize(500, 600)
        dialog.setObjectName("aiDialog")

        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Appearance Section
        appearance_label = QLabel("Appearance")
        appearance_label.setStyleSheet("font-size: 16px; font-weight: 600; margin-top: 10px;")
        layout.addWidget(appearance_label)

        # Dark Mode Toggle
        dark_mode_container = QHBoxLayout()
        dark_mode_label = QLabel("Dark Mode")
        dark_mode_label.setStyleSheet("font-size: 14px;")
        self.dark_mode_switch = ToggleSwitch()
        self.dark_mode_switch.setChecked(self.dark_mode)
        self.dark_mode_switch.stateChanged.connect(self.toggle_theme)
        dark_mode_container.addWidget(dark_mode_label)
        dark_mode_container.addStretch()
        dark_mode_container.addWidget(self.dark_mode_switch)
        layout.addLayout(dark_mode_container)

        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setStyleSheet("background-color: rgba(128, 128, 128, 0.2);")
        layout.addWidget(separator1)

        # Layout Section
        layout_label = QLabel("Layout")
        layout_label.setStyleSheet("font-size: 16px; font-weight: 600; margin-top: 10px;")
        layout.addWidget(layout_label)

        # Vertical Tabs Toggle
        vertical_tabs_container = QHBoxLayout()
        vertical_tabs_label = QLabel("Vertical Tabs")
        vertical_tabs_label.setStyleSheet("font-size: 14px;")
        self.vertical_tabs_switch = ToggleSwitch()
        self.vertical_tabs_switch.setChecked(self.vertical_tabs)
        self.vertical_tabs_switch.stateChanged.connect(self.toggle_tabs_orientation)
        vertical_tabs_container.addWidget(vertical_tabs_label)
        vertical_tabs_container.addStretch()
        vertical_tabs_container.addWidget(self.vertical_tabs_switch)
        layout.addLayout(vertical_tabs_container)

        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setStyleSheet("background-color: rgba(128, 128, 128, 0.2);")
        layout.addWidget(separator2)

        # About Section
        about_label = QLabel("About")
        about_label.setStyleSheet("font-size: 16px; font-weight: 600; margin-top: 10px;")
        layout.addWidget(about_label)

        # Version Info
        version_info = QLabel("Synth Browser v1.0\nA modern, AI-powered web browser")
        version_info.setStyleSheet("font-size: 13px; color: #808080; margin-top: 5px;")
        layout.addWidget(version_info)

        # Keyboard Shortcuts
        shortcuts_label = QLabel("Keyboard Shortcuts")
        shortcuts_label.setStyleSheet("font-size: 14px; font-weight: 600; margin-top: 15px;")
        layout.addWidget(shortcuts_label)

        shortcuts_text = QLabel(
            "• Meta+Tab - New Tab\n"
            "• Ctrl+T - New Tab\n"
            "• Ctrl+W - Close Tab\n"
            "• Ctrl+L - Focus URL Bar\n"
            "• F5 - Refresh Page\n"
            "• Alt+A - Toggle AI Chat\n"
            "• Meta+, - Settings"
        )
        shortcuts_text.setStyleSheet("font-size: 12px; color: #808080; line-height: 1.6;")
        layout.addWidget(shortcuts_text)

        layout.addStretch()

        # Close Button
        close_btn = QPushButton("Close")
        close_btn.setObjectName("sendButton")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(dialog.close)
        close_btn.setMinimumHeight(40)
        layout.addWidget(close_btn)

        dialog.exec_()

    # Tabs Orientation
    def toggle_tabs_orientation(self):
        """Toggle between horizontal and vertical tabs"""
        self.vertical_tabs = not self.vertical_tabs

        if self.vertical_tabs:
            self.tabs.setTabPosition(QTabWidget.West)
        else:
            self.tabs.setTabPosition(QTabWidget.North)

    # Theme
    def toggle_theme(self):
        """Toggle between dark and light theme"""
        self.dark_mode = not self.dark_mode
        self.apply_theme()

    def _rgba(self, hex_color, alpha):
        """Return rgba string from hex color and alpha."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            return f"rgba(91, 156, 246, {alpha})"
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"

    def build_stylesheet(self, accent, colors):
        """Compose the application stylesheet for the active theme."""
        accent_soft = self._rgba(accent, 0.26)
        accent_tint = self._rgba(accent, 0.18)
        accent_line = self._rgba(accent, 0.7)
        muted_disabled = self._rgba(colors["muted"], 0.35)

        return f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:0.6, y2:1,
                    stop:0 {colors['bg']}, stop:1 {colors['bg_gradient']});
                color: {colors['text']};
            }}
            QWidget#appRoot {{
                background: {colors['bg_gradient']};
            }}
            QWidget#contentArea {{
                background: transparent;
            }}
            QWidget#navBar {{
                background: {colors['glass']};
                border: 1px solid {colors['glass_stroke']};
                border-radius: 16px;
                padding: 6px 10px;
                margin: 12px 12px 6px 12px;
            }}
            QLabel#brandLabel {{
                color: {colors['muted_strong']};
                font-size: 15px;
                font-weight: 800;
                letter-spacing: 0.4px;
            }}
            QFrame#brandAccent {{
                background: {accent};
                border-radius: 5px;
            }}
            QLineEdit#urlBar {{
                background: {colors['panel']};
                border: 1px solid {colors['stroke']};
                border-radius: 12px;
                padding: 10px 14px;
                color: {colors['text']};
                font-size: 14px;
                selection-background-color: {accent};
            }}
            QLineEdit#urlBar:focus {{
                border: 1px solid {accent};
                background: {colors['sunken']};
            }}
            QPushButton#navButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: 12px;
                color: {colors['muted']};
                font-size: 14px;
                padding: 6px 10px;
            }}
            QPushButton#navButton:hover {{
                background: {accent_tint};
                color: {colors['text']};
                border: 1px solid {accent_tint};
            }}
            QPushButton#navButton:pressed {{
                background: {colors['sunken']};
            }}
            QPushButton#navButton:disabled {{
                color: {muted_disabled};
            }}
            QPushButton#newTabButton {{
                background: {colors['tab_inactive']};
                border: 1px dashed {colors['stroke']};
                border-radius: 12px;
                color: {colors['muted_strong']};
                font-size: 18px;
                font-weight: 700;
                min-width: 32px;
                min-height: 32px;
            }}
            QPushButton#newTabButton:hover {{
                border-color: {accent};
                color: {colors['text']};
                background: {accent_tint};
            }}
            QTabWidget::pane {{
                border: 1px solid {colors['glass_stroke']};
                background: {colors['glass']};
                border-radius: 14px;
                margin: 6px 12px 12px 12px;
            }}
            QTabBar {{
                background: transparent;
            }}
            QTabBar::tab {{
                background: {colors['tab_inactive']};
                color: {colors['muted']};
                padding: 10px 16px;
                border: 1px solid transparent;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                margin-left: 6px;
                margin-right: 6px;
                margin-top: 8px;
                min-width: 130px;
            }}
            QTabBar::tab:selected {{
                background: {colors['tab_active']};
                color: {colors['text']};
                border: 1px solid {colors['stroke']};
                border-bottom: 3px solid {accent_line};
            }}
            QTabBar::tab:hover:!selected {{
                background: {colors['hover']};
                color: {colors['text']};
                border: 1px solid {colors['stroke']};
            }}
            QTabBar::close-button {{
                subcontrol-position: right;
                width: 14px;
                height: 14px;
                margin-left: 6px;
                border-radius: 6px;
                background: transparent;
            }}
            QTabBar::close-button:hover {{
                background: {accent_tint};
            }}
            QStatusBar {{
                background: {colors['glass']};
                color: {colors['muted']};
                border: 1px solid {colors['glass_stroke']};
                border-radius: 12px;
                margin: 0px 12px 12px 12px;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QDialog#aiDialog {{
                background: {colors['glass']};
                border: 1px solid {colors['glass_stroke']};
                border-radius: 14px;
            }}
            QTextEdit#chatOutput {{
                background: {colors['panel']};
                border: 1px solid {colors['stroke']};
                border-radius: 12px;
                color: {colors['text']};
                padding: 14px;
            }}
            QLineEdit#chatInput {{
                background: {colors['panel']};
                border: 1px solid {colors['stroke']};
                border-radius: 10px;
                padding: 12px 14px;
                color: {colors['text']};
                font-size: 14px;
            }}
            QLineEdit#chatInput:focus {{
                border: 1px solid {accent};
                background: {colors['sunken']};
            }}
            QPushButton#sendButton, QPushButton#chatSendButton {{
                background: {accent};
                color: #ffffff;
                border: none;
                border-radius: 10px;
                padding: 11px 20px;
                font-weight: 700;
                font-size: 14px;
            }}
            QPushButton#sendButton:hover, QPushButton#chatSendButton:hover {{
                background: {accent_line};
            }}
            QPushButton#sendButton:pressed, QPushButton#chatSendButton:pressed {{
                background: {accent_soft};
            }}
            QPushButton#chatClearButton {{
                background: {colors['panel']};
                color: {colors['muted_strong']};
                border: 1px solid {colors['stroke']};
                border-radius: 8px;
                font-size: 13px;
                padding: 10px 14px;
            }}
            QPushButton#chatClearButton:hover {{
                background: {colors['hover']};
            }}
            QWidget#chatSlidePanel {{
                background: {colors['chat_bg']};
                border-left: 1px solid {colors['glass_stroke']};
            }}
            QWidget#chatHeader {{
                background: {colors['glass']};
                border-bottom: 1px solid {colors['glass_stroke']};
            }}
            QPushButton#chatCloseButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                color: {colors['muted']};
                font-size: 18px;
            }}
            QPushButton#chatCloseButton:hover {{
                background: {accent_tint};
                color: {colors['text']};
            }}
            QScrollArea#imageScrollArea {{
                background: {colors['panel']};
                border: 1px solid {colors['stroke']};
                border-radius: 10px;
            }}
            QListWidget#bookmarksList, QListWidget#historyList {{
                background: {colors['panel']};
                border: 1px solid {colors['stroke']};
                border-radius: 10px;
                color: {colors['text']};
                padding: 8px;
            }}
            QListWidget#bookmarksList::item, QListWidget#historyList::item {{
                padding: 10px;
                border-radius: 8px;
                margin: 2px 0px;
            }}
            QListWidget#bookmarksList::item:hover, QListWidget#historyList::item:hover {{
                background: {colors['hover']};
            }}
            QListWidget#bookmarksList::item:selected, QListWidget#historyList::item:selected {{
                background: {accent};
                color: #ffffff;
            }}
            QPushButton {{
                background: {colors['panel']};
                color: {colors['muted_strong']};
                border: 1px solid {colors['stroke']};
                border-radius: 10px;
                padding: 10px 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {accent_tint};
                color: {colors['text']};
                border-color: {accent_tint};
            }}
            QPushButton:pressed {{
                background: {colors['sunken']};
            }}
            QFrame[frameShape="4"] {{
                background: {colors['stroke']};
                max-width: 1px;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 12px;
                margin: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {colors['hover']};
                border-radius: 6px;
                min-height: 28px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {accent_tint};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QProgressBar#loadProgress {{
                border: none;
                background: {colors['sunken']};
                height: 4px;
            }}
            QProgressBar#loadProgress::chunk {{
                background: {accent};
                border-radius: 2px;
            }}
        """

    def apply_theme(self):
        """Apply current theme colors across the UI."""
        accent = self.accent_color

        if self.dark_mode:
            colors = {
                "bg": "#060a12",
                "bg_gradient": "#0b1220",
                "panel": "rgba(15, 20, 32, 0.68)",
                "card": "rgba(18, 22, 32, 0.7)",
                "stroke": "rgba(255, 255, 255, 0.10)",
                "text": "#e8edf5",
                "muted": "#9eaec7",
                "muted_strong": "#e8edf5",
                "hover": "rgba(255, 255, 255, 0.07)",
                "sunken": "rgba(255, 255, 255, 0.04)",
                "chat_bg": "rgba(10, 14, 24, 0.72)",
                "glass": "rgba(18, 24, 36, 0.55)",
                "glass_stroke": "rgba(255, 255, 255, 0.12)",
                "tab_active": "rgba(22, 28, 44, 0.72)",
                "tab_inactive": "rgba(10, 14, 24, 0.35)",
            }
        else:
            colors = {
                "bg": "#e8edf7",
                "bg_gradient": "#f6f9ff",
                "panel": "rgba(255, 255, 255, 0.6)",
                "card": "rgba(255, 255, 255, 0.75)",
                "stroke": "rgba(15, 23, 42, 0.14)",
                "text": "#0f172a",
                "muted": "#6b7280",
                "muted_strong": "#111827",
                "hover": "rgba(15, 23, 42, 0.05)",
                "sunken": "rgba(15, 23, 42, 0.03)",
                "chat_bg": "rgba(255, 255, 255, 0.78)",
                "glass": "rgba(255, 255, 255, 0.55)",
                "glass_stroke": "rgba(15, 23, 42, 0.16)",
                "tab_active": "rgba(255, 255, 255, 0.82)",
                "tab_inactive": "rgba(255, 255, 255, 0.4)",
            }

        self.setStyleSheet(self.build_stylesheet(accent, colors))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Synth Browser")

    # Set application font - clean, modern sans with platform-friendly fallbacks
    if sys.platform == "darwin":
        font = QFont("SF Pro Text", 13, QFont.Medium)
        if not QFontInfo(font).exactMatch():
            font = QFont("Helvetica Neue", 13, QFont.Medium)
    elif sys.platform == "win32":
        font = QFont("Segoe UI Variable Text", 10)
        if not QFontInfo(font).exactMatch():
            font = QFont("Segoe UI", 10)
    else:
        font = QFont("Inter", 10)
        if not QFontInfo(font).exactMatch():
            font = QFont("Noto Sans", 10)
    app.setFont(font)

    window = Synth()
    window.show()
    sys.exit(app.exec_())
