from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

CALENDAR_ID = os.environ["CALENDAR_ID"]


def main():
    # https://developers.google.com/calendar/quickstart/python

    try:
        bodies = _create_event_bodies_from_md()  # body: event id (str), game_name (str), played on (List[str])

        current_events = None
        if os.path.exists("events.json"):
            current_events = _read_events_from_json()

        service = build("calendar", "v3", credentials=_gen_googleapi_creds())
        if current_events is None:
            _create_events(service, bodies)
        else:
            bodies_create, bodies_update = _organize(bodies, current_events)
            _create_events(service, bodies_create)
            _update_events(service, bodies_update)
    except HttpError as error:
        print(f"An error occurred: {error}")


def _gen_googleapi_creds():
    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_file = "token.json"
    creds_file = "credentials.json"
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_file, "w") as token:
            token.write(creds.to_json())

    return creds


def _create_event_bodies_from_md():
    pass


def _read_events_from_json():
    pass


def _organize():
    pass


def _create_events():
    pass


def _update_events():
    pass


if __name__ == "__main__":
    main()
