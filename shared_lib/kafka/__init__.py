"""
shared_lib.kafka
================
Reusable Kafka producer, consumer, event schema, and topic constants
shared across all microservices in the HomeHaven platform.

Usage (Producer):
    from shared_lib.kafka.producer import KafkaEventProducer
    from shared_lib.kafka.topics import Topics
    from shared_lib.kafka.events import build_event

    producer = KafkaEventProducer()
    event = build_event("UserRegistered", user_id, "auth_service", payload)
    producer.publish(Topics.AUTH_USER_REGISTERED, event)

Usage (Consumer):
    from shared_lib.kafka.consumer import BaseKafkaConsumer
    class MyConsumer(BaseKafkaConsumer):
        def handle(self, event): ...
"""
