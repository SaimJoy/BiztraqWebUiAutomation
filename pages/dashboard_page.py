import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from helpers.locators import LocatorHelpers


class DashboardPage(LocatorHelpers):
    def open_case_management(self, page):
        dash_tiles = page.locator("app-solution-dashboard solution-item-view")
        dash_tiles.first.wait_for(state="visible", timeout=40000)
        case_tile = dash_tiles.first
        for i in range(dash_tiles.count()):
            text = dash_tiles.nth(i).inner_text().lower()
            if "case" in text and "management" in text and "admin" not in text:
                case_tile = dash_tiles.nth(i)
                break
        case_tile.click()
        print("Case Managemnt Found")
        page.locator("xpath=//app-solution-landing-view//solution-item-view[contains(., 'Referrals')]").first.wait_for(
            state="visible", timeout=40000
        )
        time.sleep(5)

    def open_dashboard_tile(self, page, keyword):
        dash_tiles = page.locator("app-solution-dashboard solution-item-view")
        dash_tiles.first.wait_for(state="visible", timeout=40000)
        time.sleep(2)
        names = [t.replace("\n", " ").strip() for t in dash_tiles.all_inner_texts()]
        print("Dashboard tiles:", names)
        wanted = keyword.lower().replace(" ", "").replace("-", "")
        for i in range(dash_tiles.count()):
            name = dash_tiles.nth(i).inner_text().replace("\n", " ").strip()
            compact = name.lower().replace(" ", "").replace("-", "")
            if wanted in compact:
                dash_tiles.nth(i).click()
                print(f"Opened dashboard tile: {name}")
                time.sleep(5)
                return name
        raise RuntimeError(f"No dashboard tile matching '{keyword}'. Seen: {names}")

    def click_solution_tile(self, page, keyword):
        tiles = page.locator("app-solution-landing-view app-solution-home solution-item-view")
        tiles.first.wait_for(state="visible", timeout=40000)
        time.sleep(2)
        names = [t.replace("\n", " ").strip() for t in tiles.all_inner_texts()]
        print("Solution tiles:", names)

        def title_of(full_name):
            parts = full_name.split(" ", 1)
            return parts[1] if len(parts) > 1 else full_name

        def matches(title):
            t = title.lower().strip()
            if keyword == "Referral":
                return "referral" in t and "pi" in t and "insurance" not in t and "ccm" not in t
            if keyword == "Visit":
                return t == "visits"
            if keyword == "Active":
                return t == "active cases"
            return keyword.lower() in t

        for i in range(tiles.count()):
            name = tiles.nth(i).inner_text().replace("\n", " ").strip()
            if matches(title_of(name)):
                tiles.nth(i).click()
                print(f"Opened tile: {name}")
                time.sleep(5)
                return
        raise RuntimeError(f"No solution tile matching '{keyword}'. Seen: {names}")

    def wait_for_grid(self, page, label):
        page.locator("documents").first.wait_for(state="visible", timeout=60000)
        try:
            page.locator("xpath=//*[contains(normalize-space(.), 'Loading records')]").first.wait_for(
                state="hidden", timeout=60000
            )
        except PlaywrightTimeoutError:
            print(f"{label} still shows Loading records...; continuing")
        time.sleep(8)
        print(f"{label} grid loaded")

    def back_to_solution_home(self, page):
        home = page.locator("xpath=//app-solution-landing-view//solution-item-view[contains(., 'Referrals')]")
        if home.count() and home.first.is_visible() and page.locator("documents").count() == 0:
            print("Already on Case Management home")
            return
        crumb = page.locator(
            "xpath=//*[self::a or self::span or self::button or self::div][normalize-space()='Case Management']"
        )
        el = self.first_visible(crumb, timeout=5000)
        if el is None:
            raise RuntimeError("Could not find Case Management back control")
        el.click()
        print("Clicked title-bar back control: Case Management")
        home.first.wait_for(state="visible", timeout=40000)
        time.sleep(5)
        print("Returned to Case Management home")
