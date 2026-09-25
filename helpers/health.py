import time


class HealthMonitor:
    """Track slow HTTP calls, page errors, and visible BizDRIVE error text."""

    def __init__(self, page, slow_ms=5000):
        self.slow_ms = slow_ms
        self.slow = []
        self.failed = []
        self.console = []
        self.page_errors = []
        self.ui_errors = []
        self.op_times = []
        page.on("console", self._on_console)
        page.on("pageerror", self._on_pageerror)
        page.on("response", self._on_response)

    def _on_console(self, msg):
        if msg.type in ("error", "warning"):
            text = msg.text
            if text and "favicon" not in text.lower():
                self.console.append(text[:300])

    def _on_pageerror(self, err):
        self.page_errors.append(str(err)[:300])

    def _on_response(self, response):
        try:
            url = response.url
            if any(skip in url for skip in (".woff", ".png", ".svg", "favicon", ".css", ".js.map")):
                return
            status = response.status
            timing = response.request.timing or {}
            elapsed = (timing.get("responseEnd") or 0) - (timing.get("startTime") or 0)
            if elapsed <= 0:
                elapsed = 0
            if status >= 400:
                self.failed.append({"status": status, "url": url[:180], "ms": round(elapsed)})
            elif elapsed >= self.slow_ms:
                self.slow.append({"status": status, "url": url[:180], "ms": round(elapsed)})
        except Exception:
            pass

    def record_op(self, name, seconds):
        self.op_times.append((name, seconds))
        if seconds >= 20:
            print(f"SLOW OP: {name} took {seconds:.1f}s")

    def scan_ui(self, page):
        texts = page.evaluate(
            """() => {
              const nodes = document.querySelectorAll(
                'mat-snack-bar-container, .k-notification, .toast, .error, mat-error, .mat-error, .alert'
              );
              return [...nodes].map(n => (n.innerText || '').replace(/\\s+/g, ' ').trim()).filter(Boolean);
            }"""
        )
        body = page.evaluate(
            "() => (document.body.innerText || '').slice(0, 8000)"
        ) or ""
        for t in texts:
            if t not in self.ui_errors:
                self.ui_errors.append(t)
        lowered = body.lower()
        for token in (
            "timeout",
            "timed out",
            "too slow",
            "slowness",
            "request failed",
            "server error",
            "internal server",
            "unavailable",
            "try again",
            "504",
            "503",
            "502",
        ):
            if token in lowered:
                snippet = f"page text contains '{token}'"
                if snippet not in self.ui_errors:
                    self.ui_errors.append(snippet)

    def report(self):
        print("----- BizDRIVE health -----")
        print(f"Slow HTTP (>= {self.slow_ms} ms): {len(self.slow)}")
        for item in self.slow[-15:]:
            print(f"  {item['ms']}ms {item['status']} {item['url']}")
        print(f"Failed HTTP (>=400): {len(self.failed)}")
        for item in self.failed[-15:]:
            print(f"  {item['status']} {item['url']}")
        print(f"Console errors/warnings: {len(self.console)}")
        for t in self.console[-10:]:
            print(f"  {t}")
        print(f"Page errors: {len(self.page_errors)}")
        for t in self.page_errors[-10:]:
            print(f"  {t}")
        print(f"UI error/slowness text: {len(self.ui_errors)}")
        for t in self.ui_errors:
            print(f"  {t}")
        if self.op_times:
            slow_ops = [x for x in self.op_times if x[1] >= 20]
            avg = sum(s for _, s in self.op_times) / len(self.op_times)
            print(f"Timed ops: {len(self.op_times)}, avg {avg:.1f}s, slow ops (>=20s) {len(slow_ops)}")
            for name, sec in slow_ops[-15:]:
                print(f"  {sec:.1f}s {name}")
        if not self.slow and not self.failed and not self.page_errors and not self.ui_errors:
            print("No system slowness or error signals captured.")
        else:
            print("Slowness or errors were captured — see lists above.")
        print("----- end health -----")
