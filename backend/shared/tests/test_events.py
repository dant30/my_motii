"""Tests for immutable events and synchronous dispatch."""

from uuid import uuid4

from my_motii_shared.events import DomainEvent, EventBus, SaleCompleted
from my_motii_shared.domain.money import Money


def test_event_bus_dispatches_to_subscriber_once():
    bus = EventBus()
    seen = []
    event = DomainEvent(tenant_id=uuid4(), payload={"sale_id": "s1"})
    bus.subscribe(DomainEvent, seen.append)
    bus.subscribe(DomainEvent, seen.append)

    bus.publish(event)

    assert seen == [event]
    assert event.event_type == "DomainEvent"


def test_base_event_subscription_receives_domain_subclass():
    bus = EventBus()
    seen = []
    event = SaleCompleted(sale_id=uuid4(), total=Money(500, "KES"))
    bus.subscribe(DomainEvent, seen.append)

    bus.publish(event)

    assert seen == [event]