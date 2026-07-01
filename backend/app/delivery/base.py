from abc import ABC, abstractmethod


class Notifier(ABC):
    """Sends a rendered digest through one delivery channel."""

    name: str

    @abstractmethod
    async def send_digest(self, subject: str, text_body: str, html_body: str | None) -> bool:
        """Returns True if the send succeeded."""
        ...
