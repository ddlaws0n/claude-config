#!/usr/bin/env python3
"""
Notification utilities for Claude Code hooks.
Supports desktop notifications, Slack, Discord, and other platforms.
"""

import os
import platform
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional


class NotifierBase:
    """Base class for notification systems."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def is_available(self) -> bool:
        """Check if the notification system is available."""
        raise NotImplementedError

    def send(self, title: str, message: str, urgency: str = "normal") -> bool:
        """Send a notification."""
        raise NotImplementedError


class DesktopNotifier(NotifierBase):
    """Desktop notification system."""

    def is_available(self) -> bool:
        """Check if desktop notifications are available."""
        system = platform.system()
        if system == "Darwin":  # macOS
            return True  # osascript is always available
        elif system == "Linux":
            return shutil.which("notify-send") is not None
        elif system == "Windows":
            try:
                import importlib.util

                win10toast_spec = importlib.util.find_spec("win10toast")
                return win10toast_spec is not None
            except (ImportError, ValueError):
                return False
        return False

    def send(self, title: str, message: str, urgency: str = "normal") -> bool:
        """Send desktop notification."""
        try:
            system = platform.system()

            if system == "Darwin":  # macOS
                # Determine sound based on urgency
                sound = "Glass" if urgency == "critical" else "Ping"

                # Build AppleScript command
                script = f'''
                display notification "{message}" with title "{title}" subtitle "Claude Code" sound name "{sound}"
                '''

                result = subprocess.run(
                    ["osascript", "-e", script], capture_output=True, text=True
                )
                return result.returncode == 0

            elif system == "Linux":
                # Map urgency to notify-send urgency
                urgency_map = {"low": "low", "normal": "normal", "critical": "critical"}
                notify_urgency = urgency_map.get(urgency, "normal")

                # Choose icon based on urgency
                icon_map = {
                    "low": "dialog-information",
                    "normal": "dialog-information",
                    "critical": "dialog-error",
                }
                icon = icon_map.get(urgency, "dialog-information")

                result = subprocess.run(
                    ["notify-send", "-u", notify_urgency, "-i", icon, title, message],
                    capture_output=True,
                )
                return result.returncode == 0

            elif system == "Windows":
                try:
                    import win10toast

                    toaster = win10toast.ToastNotifier()
                    toaster.show_toast(title, message, duration=5, threaded=True)
                    return True
                except Exception:
                    return False

        except Exception as e:
            print(f"Desktop notification failed: {e}", file=sys.stderr)
            return False

        return False


class SlackNotifier(NotifierBase):
    """Slack webhook notification system."""

    def __init__(self, webhook_url: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.webhook_url = webhook_url

    def is_available(self) -> bool:
        """Check if Slack webhook is configured."""
        return bool(self.webhook_url)

    def send(self, title: str, message: str, urgency: str = "normal") -> bool:
        """Send Slack notification."""
        try:
            import requests

            # Choose color based on urgency
            color_map = {
                "low": "#36a64f",  # green
                "normal": "#2196f3",  # blue
                "critical": "#ff0000",  # red
            }
            color = color_map.get(urgency, "#2196f3")

            payload = {
                "text": title,
                "attachments": [
                    {"color": color, "text": message, "ts": datetime.now().timestamp()}
                ],
            }

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200

        except Exception as e:
            print(f"Slack notification failed: {e}", file=sys.stderr)
            return False


class DiscordNotifier(NotifierBase):
    """Discord webhook notification system."""

    def __init__(self, webhook_url: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.webhook_url = webhook_url

    def is_available(self) -> bool:
        """Check if Discord webhook is configured."""
        return bool(self.webhook_url)

    def send(self, title: str, message: str, urgency: str = "normal") -> bool:
        """Send Discord notification."""
        try:
            import requests

            # Choose color based on urgency
            color_map = {
                "low": 3066993,  # green
                "normal": 3447003,  # blue
                "critical": 15158332,  # red
            }
            color = color_map.get(urgency, 3447003)

            payload = {
                "embeds": [
                    {
                        "title": title,
                        "description": message,
                        "color": color,
                        "timestamp": datetime.now().isoformat(),
                    }
                ]
            }

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 204

        except Exception as e:
            print(f"Discord notification failed: {e}", file=sys.stderr)
            return False


class EmailNotifier(NotifierBase):
    """Email notification system."""

    def __init__(self, smtp_config: Dict[str, Any]):
        super().__init__(smtp_config)

    def is_available(self) -> bool:
        """Check if email configuration is complete."""
        required = ["server", "port", "username", "password", "to"]
        return all(k in self.config for k in required)

    def send(self, title: str, message: str, urgency: str = "normal") -> bool:
        """Send email notification."""
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.config["username"]
            msg["To"] = self.config["to"]
            msg["Subject"] = f"Claude Code: {title}"

            # Add body
            body = f"""
            <html>
                <body>
                    <h2>{title}</h2>
                    <p>{message}</p>
                    <hr>
                    <p><small>Sent by Claude Code at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</small></p>
                </body>
            </html>
            """

            msg.attach(MIMEText(body, "html"))

            # Send email
            server = smtplib.SMTP(self.config["server"], self.config["port"])
            if self.config.get("use_tls", True):
                server.starttls()
            server.login(self.config["username"], self.config["password"])
            server.send_message(msg)
            server.quit()

            return True

        except Exception as e:
            print(f"Email notification failed: {e}", file=sys.stderr)
            return False


class SoundNotifier:
    """Sound notification system."""

    def __init__(self):
        self.system = platform.system()

    def is_available(self) -> bool:
        """Check if sound playback is available."""
        if self.system == "Darwin":
            return shutil.which("afplay") is not None
        elif self.system == "Linux":
            return shutil.which("paplay") is not None or shutil.which("aplay") is not None
        elif self.system == "Windows":
            return True  # Windows has built-in sound
        return False

    def play(self, sound_name: str = "default") -> bool:
        """Play a notification sound."""
        try:
            if self.system == "Darwin":  # macOS
                sound_map = {
                    "default": "Glass",
                    "error": "Basso",
                    "success": "Ping",
                    "warning": "Tink",
                }
                sound = sound_map.get(sound_name, "Glass")

                # Try system sounds first
                system_sounds = f"/System/Library/Sounds/{sound}.aiff"
                if os.path.exists(system_sounds):
                    subprocess.run(["afplay", system_sounds], capture_output=True)
                    return True

            elif self.system == "Linux":
                # Try paplay (PulseAudio)
                if shutil.which("paplay") is not None:
                    sound_files = [
                        "/usr/share/sounds/freedesktop/stereo/message.oga",
                        "/usr/share/sounds/freedesktop/stereo/dialog-information.oga",
                        "/usr/share/sounds/freedesktop/stereo/bell.oga",
                    ]
                    for sound_file in sound_files:
                        if os.path.exists(sound_file):
                            subprocess.run(["paplay", sound_file], capture_output=True)
                            return True

                # Try aplay (ALSA)
                elif shutil.which("aplay") is not None:
                    pass  # Could implement aplay fallback

            elif self.system == "Windows":
                import winsound

                sound_map = {
                    "default": winsound.MB_ICONINFORMATION,
                    "error": winsound.MB_ICONERROR,
                    "warning": winsound.MB_ICONEXCLAMATION,
                }
                winsound.MessageBeep(sound_map.get(sound_name, winsound.MB_OK))
                return True

        except Exception:
            pass  # Fail silently

        return False


class NotificationManager:
    """Manages multiple notification systems."""

    def __init__(self):
        self.notifiers: List[NotifierBase] = []
        self.sound_player = SoundNotifier()

        # Load configuration from environment
        self._load_config()

    def _load_config(self):
        """Load notification configuration from environment variables."""
        # Desktop notifications (always enabled if available)
        self.notifiers.append(DesktopNotifier())

        # Slack notifications
        slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        if slack_webhook:
            self.notifiers.append(SlackNotifier(slack_webhook))

        # Discord notifications
        discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        if discord_webhook:
            self.notifiers.append(DiscordNotifier(discord_webhook))

        # Email notifications
        if all(
            k in os.environ
            for k in [
                "SMTP_SERVER",
                "SMTP_PORT",
                "SMTP_USERNAME",
                "SMTP_PASSWORD",
                "EMAIL_TO",
            ]
        ):
            smtp_port = os.getenv("SMTP_PORT")
            email_config = {
                "server": os.getenv("SMTP_SERVER"),
                "port": int(smtp_port) if smtp_port else 587,
                "username": os.getenv("SMTP_USERNAME"),
                "password": os.getenv("SMTP_PASSWORD"),
                "to": os.getenv("EMAIL_TO"),
                "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            }
            self.notifiers.append(EmailNotifier(email_config))

    def notify(
        self,
        title: str,
        message: str,
        urgency: str = "normal",
        play_sound: bool = False,
        sound_name: str = "default",
    ) -> Dict[str, bool]:
        """
        Send notification through all available channels.

        Args:
            title: Notification title
            message: Notification message
            urgency: 'low', 'normal', or 'critical'
            play_sound: Whether to play a sound
            sound_name: Sound to play

        Returns:
            Dictionary mapping notifier name to success status
        """
        results = {}

        for notifier in self.notifiers:
            notifier_name = notifier.__class__.__name__
            try:
                success = notifier.send(title, message, urgency)
                results[notifier_name] = success
            except Exception as e:
                print(f"Notification failed ({notifier_name}): {e}", file=sys.stderr)
                results[notifier_name] = False

        # Play sound if requested
        if play_sound:
            self.sound_player.play(sound_name)

        return results

    def notify_permission_request(self, message: str):
        """Send notification for permission request."""
        self.notify(
            title="Claude Code - Permission Required",
            message=message,
            urgency="critical",
            play_sound=True,
            sound_name="warning",
        )

    def notify_idle_prompt(self, message: str):
        """Send notification for idle prompt."""
        self.notify(
            title="Claude Code", message=message, urgency="normal", play_sound=True
        )

    def notify_error(self, error: str):
        """Send error notification."""
        self.notify(
            title="Claude Code - Error",
            message=error,
            urgency="critical",
            play_sound=True,
            sound_name="error",
        )

    def notify_success(self, message: str):
        """Send success notification."""
        self.notify(
            title="Claude Code",
            message=message,
            urgency="normal",
            play_sound=True,
            sound_name="success",
        )


def main():
    """
    Command line interface for testing notifications.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Notification utilities")
    parser.add_argument("--title", default="Test", help="Notification title")
    parser.add_argument("--message", default="Test message", help="Notification message")
    parser.add_argument(
        "--urgency", choices=["low", "normal", "critical"], default="normal"
    )
    parser.add_argument("--sound", action="store_true", help="Play sound")

    args = parser.parse_args()

    manager = NotificationManager()
    results = manager.notify(
        title=args.title,
        message=args.message,
        urgency=args.urgency,
        play_sound=args.sound,
    )

    print("Notification results:")
    for name, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {name}")


if __name__ == "__main__":
    import shutil

    main()
