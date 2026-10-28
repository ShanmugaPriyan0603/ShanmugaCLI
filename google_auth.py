from pathlib import Path

from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


BASE_DIR = Path.home() / "ShanmugaCLI" / "google"

CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"


SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
]


def main():

    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    if creds and creds.valid:
        print("Google authentication already valid.")
        return

    if creds and creds.expired and creds.refresh_token:
        print("Refreshing Google authentication...")

        try:
            creds.refresh(Request())
        except RefreshError as e:
            if "invalid_grant" not in str(e):
                raise

            print("Google token expired or revoked. Starting authentication again.")
            TOKEN_FILE.unlink()
            creds = None

    if not creds or not creds.valid:
        print("Opening Google authentication...")
        print()

        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES
        )

        creds = flow.run_local_server(
            port=0,
            prompt="consent"
        )

    TOKEN_FILE.write_text(
        creds.to_json(),
        encoding="utf-8"
    )

    print()
    print("Google authentication successful.")
    print(f"Token saved to: {TOKEN_FILE}")


if __name__ == "__main__":
    main()