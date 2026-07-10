import json
from locust import HttpUser, task, between

class HackathonUser(HttpUser):
    # Simulate a user waiting between 1 to 5 seconds before asking another question
    wait_time = between(1, 5)

    @task
    def ask_rca_question(self):
        # We query the /api/stream endpoint
        payload = {
            "query": "Why is P-101 vibrating so much?",
            "role": "Engineer"
        }
        
        # In SSE (Server-Sent Events), the response is streamed.
        # Locust doesn't natively parse SSE chunks asynchronously like a browser,
        # but we can make a POST request and stream=True to read the response.
        with self.client.post(
            "/api/stream", 
            json=payload, 
            stream=True,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Read all chunks to ensure the request completes successfully
                chunks_received = 0
                for line in response.iter_lines():
                    if line:
                        chunks_received += 1
                
                if chunks_received > 0:
                    response.success()
                else:
                    response.failure("Received 200 OK but no stream data.")
            else:
                response.failure(f"Failed with status {response.status_code}")
