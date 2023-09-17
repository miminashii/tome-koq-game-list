from __future__ import print_function
from dataclasses import dataclass

import os.path
import re
import sys
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import markdown_to_json


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

CALENDAR_TIMEZONE = "Japan"
CALENDAR_ID = os.environ["CALENDAR_ID"]


def main():
    # https://developers.google.com/calendar/quickstart/python
    try:
        bodies = _create_event_bodies_from_md()

        # NOTE 一度に2500イベント取れる。ページネーションもできる。
        # https://developers.google.com/calendar/api/v3/reference/events/list?hl=ja
        current_events = _get_current_events()

        service = build("calendar", "v3", credentials=_gen_googleapi_creds())
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
    with open("../../Tome koQ Game List.md") as f:
        s = f.read()

    dictified = markdown_to_json.dictify(s)
    game_lines = list(dictified.items())[0][1][1]

    game_name_pattern = r"\[.*?\]"
    url_pattern = "https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)"
    played_on_pattern = " played on .*"

    event_bodies: List[dict] = []
    for line in game_lines:
        m = re.search(game_name_pattern, line)
        game_name = m.group().lstrip("[").rstrip("]")

        m = re.search(url_pattern, line)
        url = m.group().rstrip(")")

        m = re.search(played_on_pattern, line)
        raw_played_on = m.group()
        played_ons = raw_played_on.lstrip(" played on ").split(", ")

        if len(played_ons) == 1:
            played_on = played_ons[0]
            if "-" in played_on:
                dts = played_on.split("-")
                start_date = dts[0]
                end_date = dts[1]
            else:
                start_date = end_date = played_on
        # TODO 以下のような場合に対応できるようにする。
        # 2023/05/11-2023/05/14, 2023/05/16, 2023/05/17, 2023/05/18, 2023/05/23
        # この場合、以下のような3つの event_body が作られてほしい。
        # ・(event1) start: 2023/05/11, end: 2023/05/14 ← ハイフン繋ぎパターン
        # ・(event2) start: 2023/05/16, end: 2023/05/17 ← 2つの連続した日付パターン（3つ以上の連続した日付はないはず... その場合ハイフン繋ぎパターンになってるはず）
        # ・(event3) start: 2023/05/23, end: 2023/05/23 ← 1つの独立した日付パターン
        #
        # elif len(played_ons) > 1:
        #     start_date = played_ons[0]
        #     if "-" in start_date:
        #         dts = start_date.split("-")
        #         start_date = dts[0]
        #     end_date = played_ons[-1]
        #     if "-" in end_date:
        #         dts = end_date.split("-")
        #         end_date = dts[1]
        else:
            print(f"不正な played_on: {played_ons}")
            sys.exit(1)

        print("==========================================")
        print(f"game_name: {game_name}")
        print(f"url: {url}")
        print(f"start_date: {start_date}")
        print(f"end_date: {end_date}")
        print("==========================================")

        event_body = {
            "summary": game_name,
            "description": url,
            "start": {
                "date": start_date.replace("-", "/"),
                "timeZone": CALENDAR_TIMEZONE,
            },
            "end": {
                "date": end_date.replace("-", "/"),
                "timeZone": CALENDAR_TIMEZONE,
            },
        }
        event_bodies.append(event_body)

    return event_bodies


def _get_current_events():
    pass


def _organize(bodies, current_events):
    pass


def _create_events(service, bodies):
    pass


def _update_events(service, bodies):
    pass


if __name__ == "__main__":
    main()
