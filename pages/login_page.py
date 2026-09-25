from config import ACCOUNTS, BASE_URL, PASSWORD, USERNAME


class LoginPage:
    def login(self, page, account=None):
        creds = ACCOUNTS[account] if account else {"username": USERNAME, "password": PASSWORD}
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=90000)
        username = page.locator("app-login input").first
        username.wait_for(state="visible")
        print("User Name Element found")
        username.fill(creds["username"])
        print(f"Username entered: {creds['username']}")

        page.locator("xpath=//app-login//button[contains(normalize-space(.), 'Next')]").click()
        print("Next button clicked.")

        pwd = page.locator("app-login input[type='password']")
        pwd.first.wait_for(state="visible", timeout=20000)
        print("Password Element found")
        pwd.first.fill(creds["password"])
        print("Password entered.")

        page.locator("xpath=//app-login//button[contains(normalize-space(.), 'Login')]").last.click()
        print("Login button clicked.")

        page.locator("app-main-nav-layout, mat-toolbar").first.wait_for(state="visible", timeout=20000)
        print("1. Login success")
