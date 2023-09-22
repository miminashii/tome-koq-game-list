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
        service = build("calendar", "v3", credentials=_gen_googleapi_creds())
        event_body = {
            "summary": "47都道府県名を答える都道府県クイズ",
            "description": "https://www.start-point.net/map_quiz/nihonchizu/",
            "start": {
                "date": "2023-05-20",
                "timeZone": "Japan",
            },
            "end": {
                "date": "2023-05-20",
                "timeZone": "Japan",
            },
        }

        # create event
        event = (
            service.events()
            .insert(
                calendarId=CALENDAR_ID,
                body=event_body,
            )
            .execute()
        )
        print(f"Event created: {event.get('htmlLink')}")
        print(f"Event ID: {event.get('id')}")

        # update event
        event_body_2 = {
            "summary": "47都道府県名を答える都道府県クイズ",
            "description": "https://www.start-point.net/map_quiz/nihonchizu/",
            "start": {
                "date": "2023-05-21",
                "timeZone": "Japan",
            },
            "end": {
                "date": "2023-06-11",
                "timeZone": "Japan",
            },
        }
        event2 = service.events().update(calendarId=CALENDAR_ID, eventId=event.get("id"), body=event_body_2).execute()
        print(f"Event updated: {event2.get('htmlLink')}")
        print(f"Event ID: {event2.get('id')}")
    except HttpError as error:
        print(f"An error occurred: {error}")


def _gen_googleapi_creds():
    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


if __name__ == "__main__":
    main()
