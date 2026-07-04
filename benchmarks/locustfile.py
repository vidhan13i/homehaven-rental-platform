from locust import HttpUser, task, between

class HomeHavenUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_listings(self):
        self.client.get("/listings/units/")

    @task(2)
    def view_buildings(self):
        self.client.get("/buildings/api/")

    @task(1)
    def view_applications(self):
        self.client.get("/applications/api/")

    @task(1)
    def view_notifications(self):
        self.client.get("/notifications/api/")
