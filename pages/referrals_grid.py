import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from helpers.locators import LocatorHelpers


class ReferralsGrid(LocatorHelpers):
    ADD_RECORD_XPATH = (
        "/html/body/div[1]/app-root/app-main-nav-layout/div/main-nav/mat-drawer-container/"
        "mat-drawer-content/div/app-solution-landing-view/div[2]/documents/div/div/mat-tab-group/"
        "mat-tab-header/div[2]/div/div/div[1]/div[1]/button/span[1]/mat-icon"
    )

    def click_add_record(self, page):
        add_new_rec = page.locator(f"xpath={self.ADD_RECORD_XPATH}")
        add_new_rec.click(force=True)
        print("Add record button clicked.")
        time.sleep(8)

    def dialog_root(self, page):
        modal = page.locator("mat-dialog-container").first
        modal.wait_for(state="visible", timeout=15000)
        time.sleep(6)
        print("Using mat-dialog-container")
        return modal

    def visible_match(self, locator, timeout=3000):
        deadline = time.time() + timeout / 1000.0
        while time.time() < deadline:
            for i in range(locator.count()):
                el = locator.nth(i)
                try:
                    if el.is_visible():
                        return el
                except Exception:
                    continue
            time.sleep(0.2)
        return None

    def search_display_name(self, page, display_name):
        search_box = self.first_visible(
            page.locator("input.form-control.search-filter[class*='filter-10416']"), timeout=5000
        ) or self.first_visible(page.locator("input.form-control.search-filter"), timeout=2000)
        if search_box is None:
            raise RuntimeError("Display Name search box not found")
        search_box.scroll_into_view_if_needed()
        search_box.click()
        search_box.fill("")
        search_box.fill(display_name)
        time.sleep(0.5)

        search_btn = None
        for loc in (
            page.get_by_role("button", name="Search (Enter)"),
            page.get_by_title("Search (Enter)"),
            page.get_by_label("Search (Enter)"),
            page.locator("xpath=//*[@title='Search (Enter)' or @aria-label='Search (Enter)' or contains(@mattooltip, 'Search (Enter)')]"),
            page.locator("xpath=//*[self::button or self::a or @role='button'][contains(normalize-space(.), 'Search (Enter)')]"),
            page.locator("xpath=//*[contains(normalize-space(.), 'Search (Enter)')]"),
        ):
            search_btn = self.visible_match(loc, timeout=800)
            if search_btn is not None:
                break

        if search_btn is not None:
            try:
                search_btn.click()
            except Exception:
                search_btn.click(force=True)
            print(f"Searched Display Name for: {display_name} via Search (Enter)")
        else:
            search_box.press("Enter")
            print(f"Search (Enter) button not visible; pressed Enter for: {display_name}")
        time.sleep(5)
        try:
            page.locator("xpath=//*[contains(normalize-space(.), 'Loading records')]").first.wait_for(
                state="hidden", timeout=20000
            )
        except PlaywrightTimeoutError:
            pass
        page.locator(f"xpath=//*[contains(normalize-space(.), '{display_name}')]").first.wait_for(
            state="visible", timeout=20000
        )
        print("Record found in grid")

    def referral_status_header(self, page):
        nodes = page.locator("xpath=//documents//*[contains(normalize-space(.), 'Referral Status')]")
        if nodes.count() == 0:
            nodes = page.locator("xpath=//*[contains(normalize-space(.), 'Referral Status')]")
        best = None
        best_len = None
        for i in range(nodes.count()):
            el = nodes.nth(i)
            if not el.is_visible():
                continue
            text = " ".join((el.inner_text() or "").replace("*", " ").split()).lower()
            if text != "referral status" and not text.startswith("referral status"):
                continue
            if len(text) > 40:
                continue
            size = len(el.evaluate("e => e.outerHTML") or "")
            if best is None or size < best_len:
                best = el
                best_len = size
        return best

    def is_status_filter_control(self, el):
        cls = (el.get_attribute("class") or "").lower()
        text = " ".join((el.inner_text() or "").split()).lower()
        html = ""
        try:
            html = (el.inner_html() or "").lower()
        except Exception:
            pass
        if "search-filter" in cls:
            return True
        if any(token in text or token in html for token in ("is exactly", "greater than", "less than", "is not")):
            return True
        return False

    def scroll_grid(self, page, dx=0, dy=0):
        """Scroll SlickGrid / documents viewports sideways and/or vertically."""
        return page.evaluate(
            """({ dx, dy }) => {
              const docs = document.querySelector('documents') || document.body;
              const candidates = new Set([
                ...docs.querySelectorAll('.slick-viewport'),
                ...docs.querySelectorAll('.slick-viewport-top'),
                ...docs.querySelectorAll('.slick-header'),
                ...docs.querySelectorAll('.slick-pane'),
              ]);
              for (const n of [docs, ...docs.querySelectorAll('*')]) {
                const s = getComputedStyle(n);
                const ox = s.overflowX;
                const oy = s.overflowY;
                if (dx && (ox === 'auto' || ox === 'scroll') && n.scrollWidth > n.clientWidth + 8) {
                  candidates.add(n);
                }
                if (dy && (oy === 'auto' || oy === 'scroll') && n.scrollHeight > n.clientHeight + 8) {
                  candidates.add(n);
                }
              }
              let moved = 0;
              for (const vp of candidates) {
                if (dx) {
                  const before = vp.scrollLeft;
                  vp.scrollLeft += dx;
                  moved += Math.abs(vp.scrollLeft - before);
                }
                if (dy) {
                  const before = vp.scrollTop;
                  vp.scrollTop += dy;
                  moved += Math.abs(vp.scrollTop - before);
                }
              }
              return moved;
            }""",
            {"dx": dx, "dy": dy},
        )

    def bring_status_column_onscreen(self, page, header):
        """Scroll sideways until the Referral Status header is in the visible window."""
        for step in range(20):
            in_view = header.evaluate(
                """el => {
                  const r = el.getBoundingClientRect();
                  return r.width > 0 && r.x >= 0 && r.right <= window.innerWidth - 8;
                }"""
            )
            if in_view:
                print(f"Referral Status column is on screen (sideways step {step})")
                return True
            moved = self.scroll_grid(page, dx=280, dy=0)
            print(f"Scrolling grid sideways to Referral Status ({step + 1}); moved={moved}")
            time.sleep(0.35)
            try:
                header.scroll_into_view_if_needed()
            except Exception:
                pass
        return False

    def collect_new_status_cells(self, page, header):
        header.scroll_into_view_if_needed()
        box = header.bounding_box()
        left = right = header_bottom = None
        if box is not None:
            left, right = box["x"] - 80, box["x"] + max(box["width"], 20) + 80
            header_bottom = box["y"] + box["height"]

        locators = (page.locator("documents .slick-cell").filter(has_text="New"),)
        matches = []
        seen = set()
        for loc in locators:
            count = loc.count()
            for i in range(count):
                el = loc.nth(i)
                try:
                    if self.is_status_filter_control(el):
                        continue
                    ident = el.evaluate("e => e.outerHTML.slice(0, 180)")
                    if ident in seen:
                        continue
                    seen.add(ident)
                    b = el.bounding_box()
                    if b is None:
                        continue
                    if header_bottom is not None and b["y"] <= header_bottom:
                        continue
                    if left is not None:
                        mid = b["x"] + b["width"] / 2.0
                        if not (left <= mid <= right):
                            continue
                    matches.append(el)
                except Exception:
                    continue
            if matches:
                break
        return matches

    def new_status_value(self, page, header, display_name):
        try:
            header.scroll_into_view_if_needed()
        except Exception:
            pass
        time.sleep(0.3)
        self.bring_status_column_onscreen(page, header)
        time.sleep(0.4)

        name_nodes = page.locator(
            f"xpath=//documents//*[contains(@class,'slick-cell') and contains(normalize-space(.), '{display_name}')] | "
            f"//*[contains(@class,'slick-row') and contains(normalize-space(.), '{display_name}')]"
        )
        for i in range(name_nodes.count()):
            el = name_nodes.nth(i)
            try:
                if el.evaluate("e => e.tagName").lower() in ("input", "textarea"):
                    continue
                el.scroll_into_view_if_needed()
                time.sleep(0.3)
                break
            except Exception:
                continue

        for step in range(16):
            matches = self.collect_new_status_cells(page, header)
            if matches:
                name_y = None
                for i in range(name_nodes.count()):
                    el = name_nodes.nth(i)
                    try:
                        if el.evaluate("e => e.tagName").lower() not in ("input", "textarea"):
                            nb = el.bounding_box()
                            if nb:
                                name_y = nb["y"]
                                break
                    except Exception:
                        continue
                if name_y is not None:
                    matches.sort(key=lambda e: abs((e.bounding_box() or {}).get("y", 0) - name_y))
                found = matches[0]
                found.scroll_into_view_if_needed()
                time.sleep(0.3)
                print(f"Referral Status New found after scroll step {step}")
                return found
            if step < 10:
                print(f"Referral Status New not in view; scrolling grid sideways ({step + 1})")
                self.scroll_grid(page, dx=280, dy=0)
            else:
                print(f"Referral Status New not in view; scrolling grid vertically ({step - 9})")
                self.scroll_grid(page, dx=0, dy=160)
            time.sleep(0.45)
        return None

    def click_approved_option(self, page):
        """Choose Approved — first item in the Referral Status dropdown."""
        time.sleep(1.2)

        for i in range(page.locator("select").count()):
            sel = page.locator("select").nth(i)
            try:
                if not sel.is_visible():
                    continue
                html = (sel.inner_html() or "").lower()
                if "is exactly" in html or "greater than" in html:
                    continue
                if "approved" in html:
                    sel.select_option(label="Approved")
                    print("Referral Status set to Approved via select")
                    time.sleep(2)
                    return True
            except Exception:
                continue

        option_locators = [
            page.locator("mat-option").filter(has_text="Approved"),
            page.locator(".k-list-item, .k-item, li.k-item").filter(has_text="Approved"),
            page.get_by_role("option", name="Approved"),
            page.locator("xpath=//*[self::li or self::div or @role='option'][normalize-space()='Approved']"),
            page.get_by_text("Approved", exact=True),
        ]
        for loc in option_locators:
            found = self.visible_match(loc, timeout=1200)
            if found is None:
                continue
            if self.is_status_filter_control(found):
                continue
            label = " ".join((found.inner_text() or "").split()) or "Approved"
            if "approved" not in label.lower():
                continue
            print(f"Selecting dropdown item: {label[:40]}")
            try:
                found.click()
            except Exception:
                found.click(force=True)
            print("Referral Status set to Approved")
            time.sleep(2)
            return True
        return False

    def approve_referral_status(self, page, display_name):
        """Click Referral Status value New, then select Approved from the dropdown."""
        header = self.referral_status_header(page)
        if header is None:
            raise RuntimeError("Referral Status column header not found")
        print(
            "Referral Status column found; tag=",
            header.evaluate("e => e.tagName").lower(),
            "text=",
            (header.inner_text() or "").replace("\n", " ").strip(),
        )

        new_value = self.new_status_value(page, header, display_name)
        if new_value is None:
            raise RuntimeError("Referral Status value 'New' not found")
        print(
            "Clicking Referral Status value New:",
            new_value.evaluate("e => e.tagName").lower(),
            (new_value.get_attribute("class") or "")[:80],
        )
        new_value.scroll_into_view_if_needed()
        time.sleep(0.3)
        try:
            new_value.click()
        except Exception:
            new_value.click(force=True)
        if self.click_approved_option(page):
            return
        try:
            new_value.dblclick()
        except Exception:
            new_value.click(force=True)
        if self.click_approved_option(page):
            return
        raise RuntimeError("Approved was not in the Referral Status dropdown")
