import os
import time

from playwright.sync_api import sync_playwright

from config import (
    BIZDRIVE_FOLDER_COUNT,
    BIZDRIVE_LOCAL_ROOT,
    BIZDRIVE_NESTED_PER_FOLDER,
    BIZDRIVE_SLOW_MS,
    BIZDRIVE_TOTAL_FILES,
    DEFAULT_TIMEOUT_MS,
    NAVIGATION_TIMEOUT_MS,
)
from helpers.health import HealthMonitor
from helpers.local_tree import count_pdf_files, parent_dirs
from pages.bizdrive_page import BizdrivePage
from pages.login_page import LoginPage


class bizdrive_flow:
    def __init__(self):
        self.login_page = LoginPage()
        self.bizdrive = BizdrivePage()

    def run(self):
        root = os.path.abspath(BIZDRIVE_LOCAL_ROOT)
        if (
            len(parent_dirs(root)) != BIZDRIVE_FOLDER_COUNT
            or count_pdf_files(root) != BIZDRIVE_TOTAL_FILES
        ):
            raise RuntimeError(
                f"Local upload tree is missing or incomplete: {root}. "
                "Run playwright/run_build_tree.py first."
            )
        print(f"Using existing local tree: {root}")
        print(
            f"BizDRIVE upload from {root}: {BIZDRIVE_FOLDER_COUNT} folders, "
            f"{BIZDRIVE_NESTED_PER_FOLDER} nested each, "
            f"{BIZDRIVE_TOTAL_FILES} PDF files total"
        )
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--start-maximized"])
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            page.set_default_timeout(DEFAULT_TIMEOUT_MS)
            page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
            health = HealthMonitor(page, slow_ms=BIZDRIVE_SLOW_MS)
            try:
                self.login_page.login(page, account="joy")
                time.sleep(5)
                opened = self.bizdrive.open(page)
                print(f"Bizdrive opened: {opened}")
                self._upload_local_tree(page, health, root)
                health.scan_ui(page)
                health.report()
                time.sleep(3)
            except Exception as e:
                print(f"{type(e).__name__}: {e}")
                try:
                    health.scan_ui(page)
                    health.report()
                except Exception:
                    pass
            finally:
                browser.close()

    def _upload_local_tree(self, page, health, root):
        parents = parent_dirs(root)
        if not parents:
            raise RuntimeError(f"No local folders found in {root}")
        print(
            f"Uploading all {len(parents)} parent folders and their files "
            "through the BizDRIVE Upload Folder control"
        )
        t0 = time.time()
        self.bizdrive.upload_folder_and_wait_for_toaster(page, root)
        health.record_op("upload local directory tree", time.time() - t0)
        health.scan_ui(page)
