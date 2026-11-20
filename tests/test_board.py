"""The board's HTTP API, exercised over a real loopback socket."""

import http.client
import json
import threading

from helpers import ProjectCase

import serve

TASK = "---\nid: PRJ-001\ntitle: One\n---\n\n# One\n"


class BoardCase(ProjectCase):
    def setUp(self):
        super().setUp()
        self.path = self.write_task("backlog", "PRJ-001-one.md", TASK)
        self.server = serve.make_server("127.0.0.1", 0, self.root)
        self.port = self.server.server_address[1]
        self.server.RequestHandlerClass.log_message = lambda *args: None
        thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
        )
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, method, url, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        self.addCleanup(conn.close)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        conn.request(method, url, body=data, headers=headers or {})
        res = conn.getresponse()
        return res.status, res.read()

    def save(self, content, headers=None, mtime=None, url="/api/task/backlog/PRJ-001-one.md"):
        base = {"Content-Type": "application/json"}
        base.update(headers or {})
        return self.request("POST", url, {"content": content, "mtime": mtime}, base)

    def on_disk(self):
        return self.path.read_text(encoding="utf-8")


class ReadTests(BoardCase):
    def test_tasks_endpoint_lists_the_task(self):
        status, body = self.request("GET", "/api/tasks")
        self.assertEqual(status, 200)
        self.assertEqual([t["id"] for t in json.loads(body)["tasks"]], ["PRJ-001"])

    def test_task_endpoint_returns_raw_markdown(self):
        status, body = self.request("GET", "/api/task/backlog/PRJ-001-one.md")
        self.assertEqual((status, json.loads(body)["content"]), (200, TASK))

    def test_paths_outside_tasks_are_not_served(self):
        status, _ = self.request("GET", "/api/task/backlog/..%2F..%2Fsecret.md")
        self.assertEqual(status, 404)


class WriteTests(BoardCase):
    def test_save_writes_the_file(self):
        new = TASK + "\nedited\n"
        status, _ = self.save(new, {"Origin": f"http://127.0.0.1:{self.port}"})
        self.assertEqual((status, self.on_disk()), (200, new))

    def test_save_with_a_stale_mtime_is_a_conflict(self):
        status, _ = self.save(TASK + "\nedited\n", mtime=1.0)
        self.assertEqual((status, self.on_disk()), (409, TASK))

    def test_save_without_frontmatter_is_rejected(self):
        status, _ = self.save("# no frontmatter\n")
        self.assertEqual((status, self.on_disk()), (400, TASK))


class CrossSiteProtectionTests(BoardCase):
    """A web page open in the user's browser must not be able to drive the board."""

    def test_post_from_another_origin_is_refused(self):
        status, _ = self.save(TASK + "\nhijacked\n", {"Origin": "https://evil.example"})
        self.assertEqual((status, self.on_disk()), (403, TASK))

    def test_post_that_is_not_json_is_refused(self):
        # text/plain is what a cross-site <form> or no-preflight fetch can send.
        status, _ = self.save(TASK + "\nhijacked\n", {"Content-Type": "text/plain"})
        self.assertEqual((status, self.on_disk()), (415, TASK))

    def test_request_with_a_foreign_host_header_is_refused(self):
        # DNS rebinding: evil.example resolves to 127.0.0.1, browser sends its name as Host.
        status, _ = self.request("GET", "/api/tasks", headers={"Host": f"evil.example:{self.port}"})
        self.assertEqual(status, 403)

    def test_localhost_host_header_is_accepted(self):
        status, _ = self.request("GET", "/api/tasks", headers={"Host": f"localhost:{self.port}"})
        self.assertEqual(status, 200)


class NonLoopbackBindTests(ProjectCase):
    def test_host_check_is_skipped_when_bound_beyond_loopback(self):
        # --host 0.0.0.0 is an explicit opt-in to LAN/Tailscale names we can't enumerate.
        self.assertTrue(serve.host_allowed("my-laptop.tailnet.ts.net:8765", bind_host="0.0.0.0"))
        self.assertFalse(serve.host_allowed("my-laptop.tailnet.ts.net:8765", bind_host="127.0.0.1"))

    def test_ipv6_loopback_host_header_is_accepted(self):
        self.assertTrue(serve.host_allowed("[::1]:8765", bind_host="::1"))
