from locust import HttpUser, task, between
import json
import subprocess


class HomeHavenUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # We assume benchmark_wrk is already registered and verified by run_api_benchmarks.sh
        response = self.client.post(
            "/api/auth/login/",
            json={"username": "benchmark_wrk", "password": "password123"},
        )

        if response.status_code == 200:
            token = response.json().get("access")
            self.client.headers.update({"Authorization": f"Bearer {token}"})
        else:
            print(f"Failed to login with benchmark_wrk: {response.text}")

    @task(3)
    def view_listings(self):
        self.client.get("/api/listings/units/")

    @task(3)
    def get_buildings(self):
        self.client.get("/api/buildings/buildings/")

    @task(1)
    def get_applications(self):
        self.client.get("/api/applications/applications/")

    @task(1)
    def get_notifications(self):
        self.client.get("/api/notifications/list/")
