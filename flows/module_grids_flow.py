from pages.dashboard_page import DashboardPage


class module_grids_flow:
    """Open Referrals - PI, Visits, and Active Cases; wait for each grid; return home."""

    MODULE_STOPS = (
        ("Referral", "Referrals PI"),
        ("Visit", "Visits"),
        ("Active", "Active Cases"),
    )

    def __init__(self):
        self.dashboard = DashboardPage()

    def run(self, page):
        print("Starting module grid flow: Referrals PI, Visits, Active Cases")
        self.dashboard.back_to_solution_home(page)
        for keyword, label in self.MODULE_STOPS:
            self.dashboard.click_solution_tile(page, keyword)
            self.dashboard.wait_for_grid(page, label)
            self.dashboard.back_to_solution_home(page)
        print("Module grid flow completed")
