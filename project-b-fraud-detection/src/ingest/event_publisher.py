"""Event ingest — load sample users and publish events to Kafka (B-F-01, B-F-02)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from uuid import uuid4

from src.config import settings
from src.models import EventType, UserEvent, UserProfile

logger = logging.getLogger(__name__)


def load_sample_users(path: str | None = None) -> list[UserProfile]:
    data_path = Path(path or settings.sample_data_path)
    with data_path.open(encoding="utf-8") as f:
        payload = json.load(f)
    return [UserProfile.model_validate(item) for item in payload["users"]]


def profiles_to_events(users: list[UserProfile]) -> list[UserEvent]:
    events: list[UserEvent] = []
    for user in users:
        events.append(
            UserEvent(
                event_id=f"evt-{uuid4().hex[:10]}",
                event_type=EventType.LOGIN,
                user_id=user.user_id,
                payload={"account_age_days": user.account_age_days},
            )
        )
        for listing in user.listings:
            events.append(
                UserEvent(
                    event_id=f"evt-{uuid4().hex[:10]}",
                    event_type=EventType.LISTING,
                    user_id=user.user_id,
                    payload=listing.model_dump(),
                )
            )
        if user.behavior.messages_per_5m > 0:
            events.append(
                UserEvent(
                    event_id=f"evt-{uuid4().hex[:10]}",
                    event_type=EventType.CHAT,
                    user_id=user.user_id,
                    payload=user.behavior.model_dump(),
                )
            )
        if user.report_count > 0:
            events.append(
                UserEvent(
                    event_id=f"evt-{uuid4().hex[:10]}",
                    event_type=EventType.REPORT,
                    user_id=user.user_id,
                    payload={"report_count": user.report_count},
                )
            )
    return events


def publish_events(events: list[UserEvent], dry_run: bool = False) -> int:
    topic = settings.kafka_events_topic
    if dry_run:
        for event in events:
            logger.info("[dry-run] %s -> %s (%s)", topic, event.user_id, event.event_type)
        return len(events)

    from kafka import KafkaProducer

    producer = KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
    )
    try:
        for event in events:
            producer.send(topic, event.model_dump(mode="json"))
        producer.flush()
    finally:
        producer.close()
    return len(events)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    users = load_sample_users()
    events = profiles_to_events(users)
    try:
        count = publish_events(events, dry_run=False)
        logger.info("Published %s events to %s", count, settings.kafka_events_topic)
    except Exception as exc:  # noqa: BLE001 — M1 stub allows local run without Kafka
        logger.warning("Kafka publish failed (%s). Running dry-run.", exc)
        publish_events(events, dry_run=True)


if __name__ == "__main__":
    main()
