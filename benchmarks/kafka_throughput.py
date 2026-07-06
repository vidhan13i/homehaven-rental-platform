import time
import json
import uuid
from confluent_kafka import Producer, Consumer

KAFKA_BROKER = "localhost:9092"
TOPIC = "benchmark_events"
MSG_COUNT = 10000


def delivery_report(err, msg):
    pass


def benchmark_producer():
    producer = Producer({"bootstrap.servers": KAFKA_BROKER})
    print(f"Producing {MSG_COUNT} messages to {TOPIC}...")

    start_time = time.time()
    for i in range(MSG_COUNT):
        data = {"event_id": str(uuid.uuid4()), "payload": "benchmark_test_data_" * 10}
        producer.produce(
            TOPIC, json.dumps(data).encode("utf-8"), callback=delivery_report
        )
        if i % 1000 == 0:
            producer.poll(0)

    producer.flush()
    end_time = time.time()

    duration = end_time - start_time
    throughput = MSG_COUNT / duration
    print(
        f"Producer Throughput: {throughput:.2f} msgs/sec | Total Time: {duration:.2f}s"
    )


def benchmark_consumer():
    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BROKER,
            "group.id": "benchmark_group",
            "auto.offset.reset": "earliest",
        }
    )
    consumer.subscribe([TOPIC])

    print(f"Consuming {MSG_COUNT} messages from {TOPIC}...")
    start_time = None
    count = 0

    while count < MSG_COUNT:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            continue

        if start_time is None:
            start_time = time.time()

        count += 1

    end_time = time.time()
    duration = end_time - start_time
    throughput = count / duration

    print(
        f"Consumer Throughput: {throughput:.2f} msgs/sec | Total Time: {duration:.2f}s"
    )
    consumer.close()


if __name__ == "__main__":
    benchmark_producer()
    benchmark_consumer()
