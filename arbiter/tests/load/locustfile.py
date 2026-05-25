"""
locustfile.py — Load test scenarios for Arbiter API.

Simulates realistic user behaviour:
  - 70% browse-only users (list cases, view documents)
  - 20% intake users (start a case, send messages)
  - 10% paying users (generate document, pay)

Run with:
    locust -f arbiter/tests/load/locustfile.py \
      --host=http://localhost:8000 \
      --users=50 \
      --spawn-rate=5 \
      --run-time=5m \
      --headless

For Cloud Run load test:
    locust -f arbiter/tests/load/locustfile.py \
      --host=https://arbiter-backend-xxx.asia-south1.run.app \
      --users=100 \
      --spawn-rate=10 \
      --run-time=10m
"""
from __future__ import annotations

import json
import random
import time
from locust import HttpUser, between, task, events


# ── Test data ───────────────────────────────────────────────────────────────────────────────
TEST_JWT = "Bearer test-jwt-token-replace-with-real"  # Replace for live load tests

LEGAL_MESSAGES = [
    "My landlord hasn't returned my ₹50,000 security deposit after 2 months",
    "My employer has withheld 3 months salary without any reason",
    "I bought a phone online but received a broken product and the seller won't refund",
    "I filed an RTI application 45 days ago but got no response",
    "My boss is harassing me at the workplace and HR isn't taking action",
    "A builder took ₹2 lakh advance for flat booking but now refuses to refund",
]

FOLLOW_UP_MESSAGES = [
    "It happened in Delhi",
    "The amount is ₹50,000",
    "I have the rent agreement and bank transfer proof",
    "I vacated the flat 2 months ago",
    "Yes, I've tried calling multiple times but no response",
]


class BrowseUser(HttpUser):
    """
    Simulates a user who browses the app but doesn't create cases.
    Weight: 70% of all users.
    """
    weight = 7
    wait_time = between(2, 5)

    def on_start(self):
        self.headers = {"Authorization": TEST_JWT}

    @task(5)
    def health_check(self):
        """Lightweight health probe — simulates monitoring pings."""
        self.client.get("/health", name="/health")

    @task(3)
    def list_cases(self):
        """List user's cases."""
        with self.client.get(
            "/api/cases/",
            headers=self.headers,
            name="/api/cases/ [list]",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 401):
                response.success()

    @task(1)
    def root_endpoint(self):
        self.client.get("/", name="/")


class IntakeUser(HttpUser):
    """
    Simulates a user going through the intake chat flow.
    Weight: 20% of users.
    """
    weight = 2
    wait_time = between(3, 8)

    def on_start(self):
        self.headers = {
            "Authorization": TEST_JWT,
            "Content-Type": "application/json",
        }
        self.case_id = None

    @task(1)
    def full_intake_flow(self):
        """Simulate a complete intake conversation."""
        # Step 1: Start chat
        start_time = time.time()
        message = random.choice(LEGAL_MESSAGES)

        with self.client.post(
            "/cases/chat",
            json={"message": message},
            headers=self.headers,
            name="/cases/chat [start]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.case_id = data.get("case_id")
                response.success()
            elif response.status_code == 401:
                response.success()  # Expected without real JWT
            else:
                response.failure(f"Unexpected status: {response.status_code}")

        if not self.case_id:
            return

        # Step 2: Send follow-up messages
        for i in range(random.randint(2, 4)):
            time.sleep(random.uniform(1, 3))
            follow_up = random.choice(FOLLOW_UP_MESSAGES)

            with self.client.post(
                f"/cases/{self.case_id}/message",
                json={"message": follow_up},
                headers=self.headers,
                name="/cases/{id}/message [follow-up]",
                catch_response=True,
            ) as response:
                if response.status_code in (200, 400, 401):
                    response.success()


class PayingUser(HttpUser):
    """
    Simulates a user who generates and pays for a document.
    Weight: 10% of users — the most important flow.
    """
    weight = 1
    wait_time = between(5, 15)

    def on_start(self):
        self.headers = {
            "Authorization": TEST_JWT,
            "Content-Type": "application/json",
        }

    @task(1)
    def generate_document(self):
        """Trigger document generation (synchronous)."""
        case_id = "test-case-id"  # Use a seeded test case in real load tests
        with self.client.post(
            f"/api/cases/{case_id}/generate",
            json={"document_type": "demand_letter"},
            headers=self.headers,
            name="/api/cases/{id}/generate",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 400, 401, 404):
                response.success()

    @task(1)
    def get_document(self):
        """Fetch a document."""
        doc_id = "test-doc-id"
        with self.client.get(
            f"/api/documents/{doc_id}",
            headers=self.headers,
            name="/api/documents/{id}",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 401, 404):
                response.success()


@events.quitting.add_listener
def on_quit(environment, **kwargs):
    """Print summary stats when load test ends."""
    stats = environment.stats
    print("\n" + "="*60)
    print("ARBITER LOAD TEST COMPLETE")
    print("="*60)
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Failure rate:   {stats.total.fail_ratio:.1%}")
    print(f"P50 latency:    {stats.total.get_response_time_percentile(0.5):.0f}ms")
    print(f"P95 latency:    {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"P99 latency:    {stats.total.get_response_time_percentile(0.99):.0f}ms")
    print("="*60)
