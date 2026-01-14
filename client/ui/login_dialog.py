"""Login dialog for Play Palace v9 client."""

import wx
import sys
from pathlib import Path

# Add parent directory to path to import config_manager
sys.path.insert(0, str(Path(__file__).parent.parent))
from config_manager import ConfigManager


class LoginDialog(wx.Dialog):
    """Login dialog with username and password fields."""

    def __init__(self, parent=None):
        """Initialize the login dialog."""
        super().__init__(parent, title="Play Palace Login", size=(450, 320))

        self.dev_mode = True
        # Initialize config manager
        self.config_manager = ConfigManager()

        self.username = ""
        self.password = ""
        self.server_id = None  # Selected server ID

        # Check if running as compiled executable (PyInstaller)
        self.is_frozen = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

        # Main server URL
        self.main_server_url = "wss://play-palace.ddns.net:8000"

        # If running as executable, force main server
        if self.is_frozen:
            self.server_url = self.main_server_url
        else:
            self.server_url = "ws://localhost:8000"  # Default to Local Server

        # Server options
        self.server_options = {
            "Local Server": "ws://localhost:8000",
            "Over Internet": None,  # User will provide IP and port
        }

        # Load saved credentials from config manager
        self.username = self.config_manager.get_username()
        self.password = self.config_manager.get_password()

        # Try to get last server URL
        last_server_id = self.config_manager.get_last_server_id()
        if last_server_id:
            server_info = self.config_manager.get_server_by_id(last_server_id)
            if server_info:
                self.server_url = server_info["url"]

        # Force main server if running as executable
        if self.is_frozen:
            self.server_url = self.main_server_url

        self._create_ui()
        self.CenterOnScreen()

    def _create_ui(self):
        """Create the UI components."""
        self.panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(self.panel, label="PlayPalace 11.")
        title_font = title.GetFont()
        title_font.PointSize += 4
        title_font = title_font.Bold()
        title.SetFont(title_font)
        sizer.Add(title, 0, wx.ALL | wx.CENTER, 10)

        # Server selection
        server_label = wx.StaticText(self.panel, label="&Server:")
        sizer.Add(server_label, 0, wx.LEFT | wx.TOP, 10)

        self.server_combo = wx.ComboBox(
            self.panel,
            choices=list(self.server_options.keys()),
            style=wx.CB_READONLY | wx.CB_DROPDOWN,
        )
        # Set saved server or default to Local Server
        server_name = next(
            (
                name
                for name, url in self.server_options.items()
                if url == self.server_url
            ),
            "Local Server",
        )
        self.server_combo.SetStringSelection(server_name)

        # Disable server selection if running as compiled executable
        if self.is_frozen:
            self.server_combo.Enable(False)

        sizer.Add(self.server_combo, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # IP/Port fields for "Over Internet" option
        self.ip_label = wx.StaticText(self.panel, label="&IP Address:")
        sizer.Add(self.ip_label, 0, wx.LEFT | wx.TOP, 10)

        self.ip_input = wx.TextCtrl(self.panel, value="")
        sizer.Add(self.ip_input, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        self.port_label = wx.StaticText(self.panel, label="P&ort:")
        sizer.Add(self.port_label, 0, wx.LEFT | wx.TOP, 10)

        self.port_input = wx.TextCtrl(self.panel, value="8000")
        sizer.Add(self.port_input, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # Initially hide IP/Port fields (Local Server is default)
        self._show_internet_fields(False)

        # Bind server selection change event
        self.server_combo.Bind(wx.EVT_COMBOBOX, self.on_server_change)

        # Username
        username_label = wx.StaticText(self.panel, label="&Username:")
        sizer.Add(username_label, 0, wx.LEFT | wx.TOP, 10)

        self.username_input = wx.TextCtrl(self.panel, value=self.username)
        sizer.Add(self.username_input, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # Password
        password_label = wx.StaticText(self.panel, label="&Password:")
        sizer.Add(password_label, 0, wx.LEFT | wx.TOP, 10)

        self.password_input = wx.TextCtrl(
            self.panel, style=wx.TE_PASSWORD, value=self.password
        )
        sizer.Add(self.password_input, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)

        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.login_btn = wx.Button(self.panel, wx.ID_OK, "&Login")
        self.login_btn.SetDefault()
        button_sizer.Add(self.login_btn, 0, wx.RIGHT, 5)

        if self.dev_mode and not self.is_frozen:
            self.dev_test_btn = wx.Button(
                self.panel, wx.ID_OK, "Use &Developer Test Account"
            )
            self.dev_test_btn.Bind(wx.EVT_BUTTON, self.on_test_acc)
            button_sizer.Add(self.dev_test_btn, 0, wx.RIGHT, 5)

            self.reg_test_btn = wx.Button(self.panel, wx.ID_OK, "Use &Regular Test Account")
            self.reg_test_btn.Bind(wx.EVT_BUTTON, self.on_test_acc)
            button_sizer.Add(self.reg_test_btn, 0, wx.RIGHT, 5)

        self.create_account_btn = wx.Button(self.panel, label="Create &Account")
        button_sizer.Add(self.create_account_btn, 0, wx.RIGHT, 5)

        cancel_btn = wx.Button(self.panel, wx.ID_CANCEL, "&Cancel")
        button_sizer.Add(cancel_btn, 0)

        sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)

        # Set sizer
        self.panel.SetSizer(sizer)

        # Bind events
        self.login_btn.Bind(wx.EVT_BUTTON, self.on_login)
        self.create_account_btn.Bind(wx.EVT_BUTTON, self.on_create_account)
        cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)

        # Set focus to username (or password if username is pre-filled)
        if self.username_input.GetValue():
            self.password_input.SetFocus()
        else:
            self.username_input.SetFocus()

    def _show_internet_fields(self, show: bool):
        """Show or hide the IP/Port input fields."""
        self.ip_label.Show(show)
        self.ip_input.Show(show)
        self.port_label.Show(show)
        self.port_input.Show(show)
        self.panel.Layout()
        self.Layout()

    def on_server_change(self, event):
        """Handle server selection change."""
        server_choice = self.server_combo.GetStringSelection()
        show_fields = server_choice == "Over Internet"
        self._show_internet_fields(show_fields)

    def _validate_and_build_server_url(self) -> str | None:
        """Validate IP input and build the server URL.

        Returns:
            The server URL if valid, None if validation failed (error shown to user).
        """
        ip_address = self.ip_input.GetValue().strip()
        port = self.port_input.GetValue().strip()

        if not ip_address:
            wx.MessageBox("Please enter an IP address", "Error", wx.OK | wx.ICON_ERROR)
            self.ip_input.SetFocus()
            return None

        if not port:
            wx.MessageBox("Please enter a port", "Error", wx.OK | wx.ICON_ERROR)
            self.port_input.SetFocus()
            return None

        # Check if there's a URI scheme
        if "://" in ip_address:
            # Extract the scheme
            scheme = ip_address.split("://")[0].lower()
            if scheme not in ("ws", "wss"):
                wx.MessageBox(
                    f"Invalid URI scheme: '{scheme}://'\n\nOnly 'ws://' and 'wss://' are supported.",
                    "Invalid Server Address",
                    wx.OK | wx.ICON_ERROR,
                )
                self.ip_input.SetFocus()
                return None
            # Use the address as-is (preserving ws:// or wss://)
            host_part = ip_address.split("://", 1)[1]
            server_url = f"{scheme}://{host_part}:{port}"
        else:
            # No scheme, prepend ws://
            server_url = f"ws://{ip_address}:{port}"

        return server_url

    def _handle_server_selection(self, url: str) -> str:
        """Handle server selection, potentially prompting user if multiple servers share URL.

        Args:
            url: Server URL

        Returns:
            Server ID
        """
        server_id = self.config_manager.add_or_get_server(url)

        if server_id is None:
            # Multiple servers with same URL - prompt user to choose
            servers = self.config_manager.get_servers_by_url(url)

            choices = []
            for server in servers:
                display_name = server["nickname"] or server["url"]
                last_connected = server.get("last_connected", "Never")
                choices.append(f"{display_name} (Last: {last_connected})")

            choices.append("Connect as New Server")

            dlg = wx.SingleChoiceDialog(
                self,
                f"Multiple servers found for {url}.\nWhich one are you connecting to?",
                "Select Server",
                choices,
            )

            if dlg.ShowModal() == wx.ID_OK:
                selection = dlg.GetSelection()
                dlg.Destroy()

                if selection < len(servers):
                    # Existing server selected
                    server_id = servers[selection]["server_id"]
                    self.config_manager.update_server_last_connected(server_id)
                else:
                    # "Connect as New Server" selected
                    # Prompt for nickname
                    nickname_dlg = wx.TextEntryDialog(
                        self, "Enter a nickname for this server:", "Server Nickname", ""
                    )
                    if nickname_dlg.ShowModal() == wx.ID_OK:
                        nickname = nickname_dlg.GetValue().strip() or None
                        nickname_dlg.Destroy()
                        server_id = self.config_manager.create_new_server(url, nickname)
                    else:
                        nickname_dlg.Destroy()
                        # User cancelled - create with no nickname
                        server_id = self.config_manager.create_new_server(url)
            else:
                dlg.Destroy()
                # User cancelled - just use first one
                server_id = servers[0]["server_id"]
                self.config_manager.update_server_last_connected(server_id)

        return server_id

    def on_login(self, event):
        """Handle login button click."""
        username = self.username_input.GetValue().strip()
        password = self.password_input.GetValue()
        server_choice = self.server_combo.GetStringSelection()

        if not username:
            wx.MessageBox("Please enter a username", "Error", wx.OK | wx.ICON_ERROR)
            self.username_input.SetFocus()
            return

        if not server_choice and not self.is_frozen:
            wx.MessageBox("Please select a server", "Error", wx.OK | wx.ICON_ERROR)
            self.server_combo.SetFocus()
            return

        self.username = username
        self.password = password

        # Force main server if running as executable, otherwise use selected server
        if self.is_frozen:
            self.server_url = self.main_server_url
        elif server_choice == "Over Internet":
            # Validate and build URL from IP/Port inputs
            server_url = self._validate_and_build_server_url()
            if server_url is None:
                return  # Validation failed, error already shown
            self.server_url = server_url
        else:
            self.server_url = self.server_options[server_choice]

        # Handle server selection (may prompt if multiple servers with same URL)
        self.server_id = self._handle_server_selection(self.server_url)

        # Save credentials
        self.config_manager.set_credentials(username, password)

        self.EndModal(wx.ID_OK)

    def on_test_acc(self, event):
        """Handle test account button click."""
        if not self.dev_mode or self.is_frozen:
            return
        self.username = (
            "Developer" if event.GetEventObject() == self.dev_test_btn else "User"
        )
        self.password = "d" if event.GetEventObject() == self.dev_test_btn else "u"

        # Handle "Over Internet" option
        server_choice = self.server_combo.GetStringSelection()
        if server_choice == "Over Internet":
            server_url = self._validate_and_build_server_url()
            if server_url is None:
                return  # Validation failed, error already shown
            self.server_url = server_url

        # Handle server selection (may prompt if multiple servers with same URL)
        self.server_id = self._handle_server_selection(self.server_url)

        self.EndModal(wx.ID_OK)

    def on_create_account(self, event):
        """Handle create account button click."""
        from .registration_dialog import RegistrationDialog

        # Force main server if running as executable
        if self.is_frozen:
            server_url = self.main_server_url
        else:
            server_choice = self.server_combo.GetStringSelection()
            if not server_choice:
                wx.MessageBox(
                    "Please select a server first", "Error", wx.OK | wx.ICON_ERROR
                )
                self.server_combo.SetFocus()
                return
            if server_choice == "Over Internet":
                server_url = self._validate_and_build_server_url()
                if server_url is None:
                    return  # Validation failed, error already shown
            else:
                server_url = self.server_options[server_choice]

        dlg = RegistrationDialog(self, server_url)
        dlg.ShowModal()
        dlg.Destroy()

    def on_cancel(self, event):
        """Handle cancel button click."""
        self.EndModal(wx.ID_CANCEL)

    def get_credentials(self):
        """Get the entered credentials."""
        return {
            "username": self.username,
            "password": self.password,
            "server_url": self.server_url,
            "server_id": self.server_id,
            "config_manager": self.config_manager,
        }
