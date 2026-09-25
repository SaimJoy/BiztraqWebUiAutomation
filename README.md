# Biztraq Web UI Automation

Playwright scripts for Biztraq Online:

- **MCC** — login, create a Referrals-PI record, search it, set Referral Status to Approved, then open module grids
- **BizDRIVE** — login as Joy, open BizDRIVE, upload a local folder tree, and wait for the upload toaster

Application: https://biztraqonline.com/Auth/Login

## Requirements

- Python 3.11
- Chromium for Playwright

```powershell
cd D:\BiztraqWebUiAautomation\launch_browser\playwright
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Set `PLAYWRIGHT_BROWSERS_PATH` if browsers are already installed under `%USERPROFILE%\AppData\Local\ms-playwright`. `config.py` does that automatically on Windows.

## Configuration

Edit `config.py`:

| Setting | Purpose |
|---|---|
| `ACCOUNTS` | MCC and Joy logins |
| `ACTIVE_ACCOUNT` | Default login for MCC (`mcc`) |
| `DATE_OF_BIRTH` | Digits typed into the Kendo date field (`11111990`) |
| `BIZDRIVE_LOCAL_ROOT` | Local folder to upload (`D:\BizdriveLoadTest`) |
| `BIZDRIVE_FOLDER_COUNT` | Parent folders to generate (default `500`) |
| `BIZDRIVE_NESTED_PER_FOLDER` | Nested folders per parent (default `5`) |
| `BIZDRIVE_TOTAL_FILES` | Total PDFs to generate (default `5000`) |

BizDRIVE login always uses the `joy` account. MCC uses `ACTIVE_ACCOUNT`.

## MCC flow

Creates a Referrals-PI record (First Name, Last Name, Date of Birth), searches Display Name, sets Referral Status from **New** to **Approved**, then visits Referrals-PI, Visits, and Active Cases.

```powershell
cd D:\BiztraqWebUiAautomation\launch_browser\playwright
python run_mcc.py
```

VS Code: **Python: Playwright mcc_flow**

## BizDRIVE flow

Folder creation and upload are separate.

**1. Build the local tree** (no browser):

```powershell
python run_build_tree.py
```

Creates `D:\BizdriveLoadTest` with 500 parent folders, 5 nested folders each, and 5000 PDFs.

**2. Upload to BizDRIVE**:

```powershell
python run_bizdrive.py
```

Logs in as Joy, opens **BizDRIVE BETA**, uses **Upload Folder**, confirms **Upload**, and waits for `Upload complete 5000 files uploaded.`

VS Code: **Python: Build local BizDRIVE tree**, then **Python: Playwright bizdrive_flow**

The upload script does not create files. If `D:\BizdriveLoadTest` is missing or incomplete, it tells you to run `run_build_tree.py` first.

## Project layout

```
playwright/
  run_mcc.py              MCC entry point
  run_bizdrive.py         BizDRIVE upload entry point
  run_build_tree.py       Local folder/PDF generator
  config.py               URL, accounts, BizDRIVE counts
  flows/                  MCC and BizDRIVE orchestration
  pages/                  Login, dashboard, form, grid, BizDRIVE
  helpers/                Locators, record data, health, local tree
```

Generated PDFs under `testdata/` and `D:\BizdriveLoadTest` are not committed.
