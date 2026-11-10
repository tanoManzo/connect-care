import json
import os
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

import ai_search_app


RECIPE = {"id": "test", "title": "Apple dessert"}
UPDATED_RECIPE = {"id": "test", "title": "Apple dessert for two"}
RECOMMENDATION = {
    "recipes": [RECIPE],
    "updated_recipes": [UPDATED_RECIPE],
    "recipe": RECIPE,
    "updated_recipe": UPDATED_RECIPE,
    "latest_calories_in": 0,
}


class FixtureHandler(BaseHTTPRequestHandler):
    recommendation_payloads = []

    def log_message(self, *args):
        pass

    def respond(self, body, status=200):
        self.send_response(status)
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        if self.path.endswith("/summary"):
            if "/missing/" in self.path:
                self.respond("{}", 404)
            else:
                calories = {
                    "valid": 1800,
                    "numeric-string": "1800",
                    "invalid": "invalid",
                    "negative": -1,
                    "null": None,
                }[self.path.split("/")[-2]]
                self.respond(json.dumps({"latest_metrics": {"calories_in": calories}}))
        elif "/call/run_recipe_search/" in self.path:
            self.respond("event: complete\ndata: " + json.dumps([RECOMMENDATION]) + "\n\n")
        else:
            self.respond("event: complete\ndata: " + json.dumps([[RECIPE]]) + "\n\n")

    def do_POST(self):
        payload = self.rfile.read(int(self.headers["Content-Length"]))
        if self.path.endswith("/completions"):
            self.respond(json.dumps({"choices": [{"message": {"content": json.dumps([UPDATED_RECIPE])}}]}))
        else:
            self.recommendation_payloads.append(json.loads(payload))
            self.respond('{"event_id":"fixture"}')


class RecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.address = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_trajectory_calories_and_fallback(self):
        for user_id, expected in [
            ("valid", 1800), ("numeric-string", 1800), ("missing", 0),
            ("invalid", 0), ("negative", 0), ("null", 0),
        ]:
            with self.subTest(user_id=user_id):
                environment = dict(
                    os.environ, USER_ID=user_id, USER_API_ADDRESS=self.address,
                    SEARCH_API_ADDRESS=self.address, LLM_API_ADDRESS=self.address,
                    LATEST_CALORIES="",
                )
                result = subprocess.run(
                    ["bash", str(PROJECT_DIR / "AI_search.sh")],
                    env=environment, capture_output=True, text=True, timeout=15,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                response = json.loads(result.stdout)
                self.assertEqual(response["latest_calories_in"], expected)
                self.assertEqual(response["updated_recipes"], [UPDATED_RECIPE])

    def test_recommendation_json_contract(self):
        result = subprocess.CompletedProcess([], 0, json.dumps(RECOMMENDATION), "")
        with patch("ai_search_app.subprocess.run", return_value=result) as execute:
            response = ai_search_app.recommend("user_001", "apple dessert", top_k=5.0)
        self.assertEqual(execute.call_args.args[0][0], "bash")
        self.assertEqual(execute.call_args.kwargs["env"]["TOP_K"], "5")
        self.assertEqual(response["recipe"], RECIPE)
        self.assertEqual(response["updated_recipe"], UPDATED_RECIPE)
        self.assertEqual(response["latest_calories_in"], 0)

    def test_gradio_ui_forwards_top_k(self):
        with patch("ai_search_app.recommend", return_value=RECOMMENDATION) as recommend:
            outputs = ai_search_app.run_recipe_search("user_001", "apple dessert", "en", 5)
        recommend.assert_called_once_with("user_001", "apple dessert", "en", 5)
        self.assertEqual(outputs[2], RECOMMENDATION)

    def test_shell_client_returns_api_json(self):
        result = subprocess.run(
            ["sh", str(PROJECT_DIR / "connect_care_recommendation_example.sh")],
            env=dict(os.environ, ADDRESS=self.address),
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), RECOMMENDATION)
        self.assertEqual(
            FixtureHandler.recommendation_payloads[-1]["data"],
            ["user_001", "apple dessert for 2 people, no honey", "en", 4],
        )


if __name__ == "__main__":
    unittest.main()