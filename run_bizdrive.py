"""Entry point for the Playwright Joy / Bizdrive flow."""

from flows.bizdrive_flow import bizdrive_flow

if __name__ == "__main__":
    bizdrive_flow().run()
