import ctypes
import os
import subprocess
import time

from helpers.locators import LocatorHelpers

FIND_BIZDRIVE_JS = """
() => {
  const wanted = 'bizdrive';
  const compact = (t) => (t || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const ownText = (el) => Array.from(el.childNodes)
    .filter(n => n.nodeType === 3)
    .map(n => n.textContent)
    .join(' ');
  let best = null;
  let bestLen = Infinity;
  for (const el of document.querySelectorAll('*')) {
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') continue;
    if (el.offsetWidth === 0 && el.offsetHeight === 0) continue;
    const own = compact(ownText(el));
    const text = compact(el.innerText);
    if (!own.includes(wanted) && !text.includes(wanted)) continue;
    if (text.length > 80) continue;
    const size = (el.outerHTML || '').length;
    if (size < bestLen) {
      best = el;
      bestLen = size;
    }
  }
  return best;
}
"""


class BizdrivePage(LocatorHelpers):
    def scroll_dashboard(self, page):
        for _ in range(12):
            moved = page.evaluate(
                """() => {
                  const roots = [
                    document.querySelector('app-solution-dashboard'),
                    document.querySelector('.mat-drawer-content'),
                    document.scrollingElement,
                  ].filter(Boolean);
                  let moved = 0;
                  for (const root of roots) {
                    const before = root.scrollTop;
                    root.scrollTop += 450;
                    moved += Math.abs(root.scrollTop - before);
                  }
                  window.scrollBy(0, 450);
                  return moved;
                }"""
            )
            time.sleep(0.35)
            if not moved:
                break

    def open(self, page):
        page.locator("app-solution-dashboard solution-item-view").first.wait_for(state="visible", timeout=40000)
        time.sleep(2)
        self.scroll_dashboard(page)
        time.sleep(1)

        dash_tiles = page.locator("app-solution-dashboard solution-item-view")
        names = [t.replace("\n", " ").strip() for t in dash_tiles.all_inner_texts()]
        print("Dashboard tiles:", names)

        search = self.first_visible(
            page.locator(
                "app-solution-dashboard input, input[placeholder*='Search' i], input[placeholder*='Filter' i]"
            ),
            timeout=2000,
        )
        if search is not None:
            search.click()
            search.fill("Bizdrive")
            time.sleep(1.5)
            names = [t.replace("\n", " ").strip() for t in dash_tiles.all_inner_texts()]
            print("Dashboard tiles after search:", names)
        for i in range(dash_tiles.count()):
            name = dash_tiles.nth(i).inner_text().replace("\n", " ").strip()
            compact = "".join(ch for ch in name.lower() if ch.isalnum())
            if "bizdrive" in compact:
                dash_tiles.nth(i).click()
                print(f"Opened dashboard tile: {name}")
                time.sleep(5)
                return name

        handle = page.evaluate_handle(FIND_BIZDRIVE_JS)
        el = handle.as_element()
        if el is None:
            raise RuntimeError(f"Bizdrive not found. Dashboard tiles: {names}")
        label = " ".join((el.inner_text() or "").split())
        print(f"Found Bizdrive component: {label[:80]}")
        try:
            el.click()
        except Exception:
            el.click(force=True)
        print("Bizdrive clicked")
        time.sleep(5)
        page.locator("kendo-window").filter(has_text="BizDRIVE").first.wait_for(state="visible", timeout=30000)
        return label

    def drive(self, page):
        return page.locator("kendo-window").filter(has_text="BizDRIVE").first

    def wait_drive_idle(self, page, timeout=30000):
        drive = self.drive(page)
        deadline = time.time() + timeout / 1000.0
        while time.time() < deadline:
            busy = drive.locator(
                ".k-loading-mask, .k-loading-image, mat-spinner, .spinner, .loading-overlay"
            )
            visible_busy = False
            for i in range(busy.count()):
                try:
                    if busy.nth(i).is_visible():
                        visible_busy = True
                        break
                except Exception:
                    continue
            if not visible_busy:
                return
            time.sleep(0.25)

    def dismiss_overlays(self, page):
        pane = page.locator(".cdk-overlay-pane, mat-dialog-container, .conflict-item")
        if self.first_visible(pane, timeout=400) is None:
            return
        page.keyboard.press("Escape")
        time.sleep(0.2)
        if self.first_visible(pane, timeout=400) is None:
            return
        overlay = page.locator("mat-dialog-container, .cdk-overlay-pane")
        for label in ("Close", "Cancel", "OK", "Skip", "Keep both", "Replace"):
            btn = self.first_visible(overlay.locator("button").filter(has_text=label), timeout=250)
            if btn is not None:
                try:
                    btn.click()
                except Exception:
                    btn.click(force=True)
                time.sleep(0.2)
                break

    def in_overlay(self, el):
        try:
            return el.evaluate(
                """e => {
                  let n = e;
                  while (n) {
                    const c = (n.className || '').toString();
                    const id = n.id || '';
                    if (c.includes('cdk-overlay') || c.includes('conflict-item') || id.includes('cdk-overlay')) return true;
                    n = n.parentElement;
                  }
                  return false;
                }"""
            )
        except Exception:
            return False

    def create_folder(self, page, name):
        self.dismiss_overlays(page)
        drive = self.drive(page)
        drive.locator("button[title='New Folder']").click()
        dlg = page.locator("mat-dialog-container").filter(has_text="Add Folder")
        dlg.wait_for(state="visible", timeout=15000)
        dlg.locator("input[placeholder='Enter folder name']").fill(name)
        dlg.locator("xpath=.//button[contains(normalize-space(.), 'Save')]").click()
        dlg.wait_for(state="hidden", timeout=60000)
        self.wait_drive_idle(page)
        if self.visible_named(self.drive(page).get_by_text(name, exact=True), timeout=20000) is None:
            raise RuntimeError(f"Created folder not listed: {name}")
        print(f"Created folder: {name}")

    def visible_named(self, locator, timeout=25000):
        deadline = time.time() + timeout / 1000.0
        best = None
        best_x = -1
        while time.time() < deadline:
            for i in range(locator.count()):
                el = locator.nth(i)
                try:
                    if not el.is_visible() or self.in_overlay(el):
                        continue
                    box = el.bounding_box()
                    if box and box["x"] >= best_x:
                        best = el
                        best_x = box["x"]
                except Exception:
                    continue
            if best is not None:
                return best
            time.sleep(0.25)
        return None

    def click_item(self, page, name, dbl=True):
        self.dismiss_overlays(page)
        drive = self.drive(page)
        best = self.visible_named(drive.get_by_text(name, exact=True), timeout=25000)
        if best is None:
            raise RuntimeError(f"Item not visible: {name}")
        best.scroll_into_view_if_needed()
        time.sleep(0.3)
        try:
            if dbl:
                best.dblclick()
            else:
                best.click()
        except Exception:
            if dbl:
                best.dblclick(force=True)
            else:
                best.click(force=True)
        time.sleep(0.8)
        self.wait_drive_idle(page)
        self.dismiss_overlays(page)

    def go_up(self, page):
        self.dismiss_overlays(page)
        drive = self.drive(page)
        toolbar = drive.locator(".explorer-toolbar, .cloud-drive-toolbar")
        btn = None
        for loc in (
            toolbar.get_by_text("Up", exact=True),
            drive.get_by_role("button", name="Up"),
            drive.locator("xpath=.//*[self::button or self::a or @role='button'][contains(normalize-space(.), 'Up')]"),
        ):
            btn = self.first_visible(loc, timeout=2000)
            if btn is not None:
                break
        if btn is None:
            raise RuntimeError("BizDRIVE Up control not found")
        try:
            btn.click()
        except Exception:
            btn.click(force=True)
        time.sleep(0.8)
        self.wait_drive_idle(page)

    def go_home(self, page):
        self.dismiss_overlays(page)
        drive = self.drive(page)
        home = drive.locator("xpath=.//*[normalize-space()='Home']").first
        home.click()
        time.sleep(1)
        self.wait_drive_idle(page)

    def upload_pdfs(self, page, paths):
        self.dismiss_overlays(page)
        drive = self.drive(page)
        chooser = None
        try:
            with page.expect_file_chooser(timeout=5000) as fc:
                drive.locator("button[title='Upload Files']").click()
            chooser = fc.value
        except Exception:
            drive.locator("button[title='Upload Files']").click()
        if chooser is not None:
            chooser.set_files(paths)
        else:
            drive.locator("input[type='file']").first.set_input_files(paths)
        self.wait_drive_idle(page, timeout=120000)
        time.sleep(1)
        self.dismiss_overlays(page)
        print(f"Uploaded {len(paths)} PDF file(s) from this device")

    def drag_drop_pdfs(self, page, paths):
        """Load local files into a DataTransfer and drop them on BizDRIVE."""
        self.dismiss_overlays(page)
        drive = self.drive(page)
        temp_input = page.locator("#bizdrive-local-drag-files")
        if temp_input.count() == 0:
            drive.evaluate(
                """drive => {
                  const input = document.createElement('input');
                  input.id = 'bizdrive-local-drag-files';
                  input.type = 'file';
                  input.multiple = true;
                  input.style.display = 'none';
                  drive.appendChild(input);
                }"""
            )
            temp_input = page.locator("#bizdrive-local-drag-files")
        temp_input.set_input_files(paths)
        dropped = drive.evaluate(
            """drive => {
              const input = drive.querySelector('#bizdrive-local-drag-files');
              const dt = new DataTransfer();
              for (const file of input.files) dt.items.add(file);
              const selectors = [
                '.file-explorer-content',
                '.explorer-content',
                '.cloud-drive-content',
                '.file-list',
                '.items-container',
                '[role="grid"]',
                '.k-grid-content',
              ];
              let target = null;
              for (const selector of selectors) {
                const candidate = drive.querySelector(selector);
                if (candidate && candidate.getBoundingClientRect().width > 0) {
                  target = candidate;
                  break;
                }
              }
              target ||= drive;
              for (const type of ['dragenter', 'dragover', 'drop']) {
                target.dispatchEvent(new DragEvent(type, {
                  bubbles: true,
                  cancelable: true,
                  composed: true,
                  dataTransfer: dt,
                }));
              }
              input.value = '';
              return {
                target: target.className || target.tagName,
                count: dt.files.length,
              };
            }"""
        )
        print(
            f"Drag-dropped {dropped['count']} local PDF file(s) "
            f"onto {dropped['target']}"
        )
        self.wait_drive_idle(page, timeout=120000)
        time.sleep(1.5)
        self.dismiss_overlays(page)

    def drag_drop_directory(self, page, folder_path):
        """Drop one local directory using Windows Explorer."""
        return self.windows_drag_drop_directory(page, folder_path)

    def windows_drag_drop_directory(self, page, folder_path):
        """Drag a real directory from Windows Explorer onto BizDRIVE."""
        from pywinauto import Desktop

        folder_path = os.path.abspath(folder_path)
        folder_name = os.path.basename(folder_path)
        subprocess.Popen(["explorer.exe", f"/select,{folder_path}"])
        time.sleep(6)

        explorer = None
        item = None
        desktop = Desktop(backend="uia")
        deadline = time.time() + 30
        while time.time() < deadline and item is None:
            for window in reversed(desktop.windows(class_name="CabinetWClass")):
                try:
                    for candidate in window.descendants(control_type="ListItem"):
                        if candidate.window_text().strip() == folder_name:
                            explorer = window
                            item = candidate
                            break
                    if item is not None:
                        break
                except Exception:
                    continue
            if item is None:
                time.sleep(1)
        if explorer is None or item is None:
            raise RuntimeError(
                f"Windows Explorer item not found for drag: {folder_path}"
            )

        # Keep Explorer on the left so the BizDRIVE popup remains visible.
        ctypes.windll.user32.MoveWindow(
            explorer.handle, 0, 0, 610, 820, True
        )
        explorer.set_focus()
        item.click_input()
        time.sleep(1)

        drive = self.drive(page)
        box = drive.bounding_box()
        if box is None:
            raise RuntimeError("BizDRIVE popup window has no bounding box")
        screen = page.evaluate(
            """() => ({
              x: window.screenX + (window.outerWidth - window.innerWidth) / 2,
              y: window.screenY + window.outerHeight - window.innerHeight
                - (window.outerWidth - window.innerWidth) / 2,
            })"""
        )
        target = (
            round(screen["x"] + box["x"] + box["width"] * 0.72),
            round(screen["y"] + box["y"] + box["height"] * 0.55),
        )
        print(
            f"Dragging Windows Explorer folder {folder_path} "
            f"onto BizDRIVE popup at {target}"
        )
        item.drag_mouse_input(dst=target, button="left", absolute=True)
        time.sleep(10)
        try:
            ctypes.windll.user32.ShowWindow(explorer.handle, 6)
        except Exception:
            pass

        drive.get_by_text(folder_name, exact=True).first.wait_for(
            state="visible", timeout=120000
        )
        self.wait_drive_idle(page, timeout=300000)
        print(f"BizDRIVE accepted dropped folder: {folder_name}")
        self.dismiss_overlays(page)

    def try_upload_directory(self, page, folder_path):
        self.dismiss_overlays(page)
        drive = self.drive(page)
        for sel in (
            "button[title='Upload Folder']",
            "button[title='Upload folder']",
            "button[title='Upload Directory']",
        ):
            btn = drive.locator(sel)
            if btn.count() == 0:
                continue
            try:
                with page.expect_file_chooser(timeout=4000) as fc:
                    btn.first.click()
                fc.value.set_files(folder_path)
                self.wait_drive_idle(page, timeout=300000)
                self.dismiss_overlays(page)
                print(f"Uploaded local folder: {folder_path}")
                return True
            except Exception:
                continue
        directory_input = drive.locator("input[webkitdirectory], input[directory]")
        if directory_input.count():
            directory_input.first.set_input_files(folder_path)
            self.wait_drive_idle(page, timeout=300000)
            self.dismiss_overlays(page)
            print(f"Uploaded local folder via directory input: {folder_path}")
            return True
        return False

    def upload_folder_and_wait_for_toaster(self, page, folder_path):
        """Use Upload Folder and verify BizDRIVE's confirmation toaster."""
        self.dismiss_overlays(page)
        drive = self.drive(page)
        button = drive.locator("button[title='Upload Folder']").first
        button.wait_for(state="visible", timeout=20000)

        page.evaluate(
            """() => {
              window.__bizdriveUploadToasts = [];
              const capture = () => {
                const selector = [
                  'mat-snack-bar-container',
                  '.k-notification',
                  '.toast',
                  '.toastr',
                  '[role="alert"]',
                  '.alert',
                ].join(',');
                for (const el of document.querySelectorAll(selector)) {
                  const text = (el.innerText || '').replace(/\\s+/g, ' ').trim();
                  if (text && !window.__bizdriveUploadToasts.includes(text)) {
                    window.__bizdriveUploadToasts.push(text);
                  }
                }
              };
              capture();
              window.__bizdriveToastObserver?.disconnect();
              window.__bizdriveToastObserver = new MutationObserver(capture);
              window.__bizdriveToastObserver.observe(document.body, {
                childList: true,
                subtree: true,
                characterData: true,
              });
            }"""
        )

        print(f"Clicking Upload Folder for local directory: {folder_path}")
        with page.expect_file_chooser(timeout=15000) as chooser_info:
            button.click()
        chooser_info.value.set_files(folder_path)
        confirm = self.first_visible(
            page.get_by_role("button", name="Upload", exact=True),
            timeout=120000,
        )
        if confirm is None:
            raise RuntimeError("Upload Folder confirmation button was not found")
        confirm.click()
        print("Upload Folder confirmation clicked")
        print("Local directory selected; waiting for BizDRIVE toaster confirmation")

        deadline = time.time() + 21600
        seen = set()
        while time.time() < deadline:
            messages = page.evaluate("() => window.__bizdriveUploadToasts || []")
            for message in messages:
                if message in seen:
                    continue
                seen.add(message)
                print(f"BizDRIVE toaster: {message}")
                lowered = message.lower()
                if any(word in lowered for word in ("fail", "error", "unable", "invalid")):
                    raise RuntimeError(f"BizDRIVE upload failed: {message}")
                if any(
                    word in lowered
                    for word in ("success", "uploaded", "complete", "completed")
                ):
                    self.wait_drive_idle(page, timeout=300000)
                    print(f"Upload confirmation received: {message}")
                    return message
            time.sleep(1)
        raise RuntimeError(
            "BizDRIVE did not show an upload confirmation toaster within 6 hours"
        )
