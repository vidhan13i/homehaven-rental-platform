import logging
import threading
from django.core.management.base import BaseCommand
from django.conf import settings

from notification.consumers import (
    ApplicationConsumer,
    UserConsumer,
    MessageConsumer,
    ReviewConsumer,
    ListingConsumer,
)

logger = logging.getLogger("notification.management.commands")


class Command(BaseCommand):
    help = "Run Kafka consumers for the notification service."

    def handle(self, *args, **options):
        if not settings.KAFKA_ENABLED:
            self.stdout.write(self.style.WARNING("Kafka is disabled in settings. KAFKA_ENABLED=false"))
            return

        group_id = settings.KAFKA_CONSUMER_GROUP_ID

        consumers = [
            ApplicationConsumer(group_id),
            UserConsumer(group_id),
            MessageConsumer(group_id),
            ReviewConsumer(group_id),
            ListingConsumer(group_id),
        ]

        threads = []
        for consumer in consumers:
            t = threading.Thread(target=consumer.start, daemon=True)
            threads.append(t)
            t.start()
            self.stdout.write(self.style.SUCCESS(f"Started {consumer.__class__.__name__} thread."))

        try:
            for t in threads:
                t.join()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Shutting down consumers..."))
            for consumer in consumers:
                consumer.stop()
            for t in threads:
                t.join(timeout=5)
            self.stdout.write(self.style.SUCCESS("All consumers stopped."))
