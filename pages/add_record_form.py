import time

from helpers.locators import LocatorHelpers
from pages.dashboard_page import DashboardPage


class AddRecordForm(LocatorHelpers):
    def __init__(self):
        self.dashboard = DashboardPage()

    def type_kendo_date(self, page, el, value):
        inp = el
        tag = el.evaluate("e => e.tagName").lower()
        if "k-dateinput" in (el.get_attribute("class") or "") or tag != "input":
            found = self.child_visible(el, "input.k-input-inner, input", timeout=2000)
            if found is not None:
                inp = found
        inp.scroll_into_view_if_needed()
        inp.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        page.keyboard.type(value, delay=80)
        time.sleep(0.5)
        page.keyboard.press("Tab")
        time.sleep(0.8)
        print(f"Kendo date send_keys: {value}")

    def type_into(self, page, el, value):
        el.scroll_into_view_if_needed()
        el.click()
        time.sleep(0.4)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        time.sleep(0.2)
        page.keyboard.type(value, delay=120)
        time.sleep(0.5)
        page.keyboard.press("Tab")
        time.sleep(0.8)

    def control_for_label(self, label_el):
        found = self.child_visible(
            label_el,
            "xpath=./ancestor::mat-form-field[1]//input | ./ancestor::mat-form-field[1]//textarea",
            timeout=500,
        )
        if found is not None:
            return found
        sib = self.child_visible(label_el, "xpath=./following-sibling::*[1]", timeout=500)
        if sib is not None:
            inp = self.child_visible(sib, "input, textarea", timeout=500)
            return inp if inp is not None else sib
        parent_sib = self.child_visible(label_el, "xpath=./../following-sibling::*[1]", timeout=500)
        if parent_sib is not None:
            inp = self.child_visible(parent_sib, "input, textarea", timeout=500)
            return inp if inp is not None else parent_sib
        return None

    def fill_by_exact_label(self, page, root, label_names, value, is_date=False):
        label_el = self.find_exact_label(root, label_names)
        if label_el is None:
            return False
        print(f"Found label '{self.own_text(label_el)}'")
        if is_date:
            kendo = self.child_visible(
                label_el,
                "xpath=./ancestor::*[contains(@class,'field') or contains(@class,'row') or self::mat-form-field][1]//*[contains(@class,'k-dateinput')]",
                timeout=500,
            ) or self.first_visible(root.locator(".k-dateinput"), timeout=2000)
            if kendo is None:
                return False
            self.type_kendo_date(page, kendo, value)
            return True
        control = self.control_for_label(label_el)
        if control is None:
            return False
        self.type_into(page, control, value)
        return True

    def fill_add_record_form(self, page, root, rec):
        filled = []
        fields = (
            (("First Name",), rec["first_name"]),
            (("Last Name", "Surname"), rec["last_name"]),
            (("Date of Birth", "Date Of Birth"), rec["date_of_birth"], True),
        )
        for item in fields:
            names, value = item[0], item[1]
            is_date = len(item) == 3
            if self.fill_by_exact_label(page, root, names, value, is_date=is_date):
                filled.append(names[0])
                print(f"Filled {names[0]}: {value}")
                time.sleep(1.5)
        if "First Name" not in filled or "Last Name" not in filled:
            raise RuntimeError(f"First Name / Last Name were not filled. Filled: {filled}")
        return rec["display_name"]

    def save_and_close_form(self, page):
        time.sleep(2)
        btn = page.locator(
            "xpath=//mat-dialog-container//button[contains(normalize-space(.), 'Save & Close')]"
        ).first
        btn.wait_for(state="visible", timeout=15000)
        try:
            btn.click()
        except Exception:
            btn.click(force=True)
        print("Save & Close clicked")
        time.sleep(3)
        errors = [
            loc.inner_text().strip()
            for loc in page.locator("mat-error, .mat-error").all()
            if loc.is_visible() and loc.inner_text().strip()
        ]
        if errors:
            print("Save validation errors:", errors)
        page.locator("xpath=//mat-dialog-container//button[contains(normalize-space(.), 'Save & Close')]").first.wait_for(
            state="hidden", timeout=40000
        )
        time.sleep(5)
        self.dashboard.wait_for_grid(page, "Referrals PI after save")
