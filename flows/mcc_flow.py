import time

from playwright.sync_api import sync_playwright

from config import DEFAULT_TIMEOUT_MS, NAVIGATION_TIMEOUT_MS
from flows.module_grids_flow import module_grids_flow
from helpers.record import make_random_record
from pages.add_record_form import AddRecordForm
from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from pages.referrals_grid import ReferralsGrid


class rec_creation:
    def __init__(self):
        self.login_page = LoginPage()
        self.dashboard = DashboardPage()
        self.form = AddRecordForm()
        self.grid = ReferralsGrid()
        self.module_grids = module_grids_flow()

    def mcc_flow(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--start-maximized"])
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            page.set_default_timeout(DEFAULT_TIMEOUT_MS)
            page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
            try:
                self.login_page.login(page)
                time.sleep(5)
                self.dashboard.open_case_management(page)
                self.dashboard.click_solution_tile(page, "Referral")
                self.dashboard.wait_for_grid(page, "Referrals PI")
                self.grid.click_add_record(page)
                root = self.grid.dialog_root(page)
                rec = make_random_record()
                display_name = self.form.fill_add_record_form(page, root, rec)
                self.form.save_and_close_form(page)
                self.grid.search_display_name(page, display_name)
                self.grid.approve_referral_status(page, display_name)
                self.module_grids.run(page)
                time.sleep(3)
            except Exception as e:
                print(f"{type(e).__name__}: {e}")
            finally:
                browser.close()
