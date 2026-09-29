"""Small synchronous event bus for in-process domain notifications."""

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from .base import DomainEvent

EventHandler = Callable[[DomainEvent], Any]


class EventBus:
	def __init__(self) -> None:
		self._handlers: dict[type[DomainEvent], list[EventHandler]] = defaultdict(list)

	def subscribe(self, event_class: type[DomainEvent], handler: EventHandler) -> None:
		if handler not in self._handlers[event_class]:
			self._handlers[event_class].append(handler)

	def publish(self, event: DomainEvent) -> None:
		for event_class in type(event).__mro__:
			if not issubclass(event_class, DomainEvent):
				continue
			for handler in tuple(self._handlers.get(event_class, ())):
				handler(event)