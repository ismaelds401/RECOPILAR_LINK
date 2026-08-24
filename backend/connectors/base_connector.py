"""Contract shared by independent event-source connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from backend.models.event import Event


class ConnectorError(RuntimeError):
    """A source failed without implying that other connectors must stop."""


@dataclass(frozen=True, slots=True)
class SourceDefinition:
    name: str
    base_url: str
    source_type: str
    connector: str
    priority: int = 100


class BaseConnector(ABC):
    source: SourceDefinition

    @abstractmethod
    def collect(self) -> list[Event]:
        """Fetch and normalize upcoming events from one source."""


