import os.path
import re
import sys
from datetime import datetime, timedelta
from typing import List

import markdown_to_json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

CALENDAR_TIMEZONE = "Japan"
CALENDAR_ID = os.environ["CALENDAR_ID"]


def main():
    # https://developers.google.com/calendar/quickstart/python
    try:
        bodies = _create_event_bodies_from_md()
        # print(len(bodies))
        # with open("result.json", "w") as fp:
        #     json.dump(bodies, fp, ensure_ascii=False)
        # sys.exit()

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

        # NOTE 以下のような played_ons の場合、
        # 2023/05/11-2023/05/14, 2023/05/16, 2023/05/17, 2023/05/23
        # 以下のような3つの event が作られてほしい。
        # ・(event1) start: 2023/05/11, end: 2023/05/14 ← 「2023/05/11-2023/05/14」、ハイフン繋ぎパターン
        # ・(event2) start: 2023/05/16, end: 2023/05/17 ← 「2023/05/16, 2023/05/17」、2つの連続した日付パターン（3つ以上の連続した日付はないはず... その場合ハイフン繋ぎパターンになってるはず）
        # ・(event3) start: 2023/05/23, end: 2023/05/23 ← 「2023/05/23」、1つの独立した日付パターン
        if len(played_ons) == 1:
            played_on = played_ons[0]

            # ハイフン繋ぎパターン
            if "-" in played_on:
                dts = played_on.split("-")
                start_date = dts[0]
                end_date = dts[1]
            else:
                # 1つの独立した日付パターン
                start_date = end_date = played_on

            event_body = {
                "summary": game_name,
                "description": f"ゲームのURL: {url}",
                "start": {
                    "date": start_date.replace("/", "-"),
                    "timeZone": CALENDAR_TIMEZONE,
                },
                "end": {
                    "date": end_date.replace("/", "-"),
                    "timeZone": CALENDAR_TIMEZONE,
                },
            }
            event_bodies.append(event_body)
        elif len(played_ons) > 1:
            idx = 0
            while idx <= len(played_ons) - 1:
                played_on = played_ons[idx]

                # ハイフン繋ぎパターン
                if "-" in played_on:
                    dts = played_on.split("-")
                    start_date = dts[0]
                    end_date = dts[1]
                    event_body = {
                        "summary": game_name,
                        "description": f"ゲームのURL: {url}",
                        "start": {
                            "date": start_date.replace("/", "-"),
                            "timeZone": CALENDAR_TIMEZONE,
                        },
                        "end": {
                            "date": end_date.replace("/", "-"),
                            "timeZone": CALENDAR_TIMEZONE,
                        },
                    }
                    event_bodies.append(event_body)
                    idx += 1
                else:
                    try:
                        played_on_next = played_ons[idx + 1]
                    except IndexError:
                        played_on_next = None

                    first = datetime.strptime(played_on, "%Y/%m/%d")

                    if played_on_next:
                        if "-" in played_on_next:
                            # 1つの独立した日付パターン
                            event_body = {
                                "summary": game_name,
                                "description": f"ゲームのURL: {url}",
                                "start": {
                                    "date": played_on.replace("/", "-"),
                                    "timeZone": CALENDAR_TIMEZONE,
                                },
                                "end": {
                                    "date": played_on.replace("/", "-"),
                                    "timeZone": CALENDAR_TIMEZONE,
                                },
                            }
                            event_bodies.append(event_body)

                            # ハイフン繋ぎパターン
                            dts = played_on_next.split("-")
                            start_date = dts[0]
                            end_date = dts[1]
                            event_body = {
                                "summary": game_name,
                                "description": f"ゲームのURL: {url}",
                                "start": {
                                    "date": start_date.replace("/", "-"),
                                    "timeZone": CALENDAR_TIMEZONE,
                                },
                                "end": {
                                    "date": end_date.replace("/", "-"),
                                    "timeZone": CALENDAR_TIMEZONE,
                                },
                            }
                            event_bodies.append(event_body)
                            idx += 2
                            continue

                        second = datetime.strptime(played_on_next, "%Y/%m/%d")

                        # 2つの連続した日付パターン
                        if (first + timedelta(days=1)) == second:
                            event_body = {
                                "summary": game_name,
                                "description": f"ゲームのURL: {url}",
                                "start": {
                                    "date": first.strftime("%Y-%m-%d"),
                                    "timeZone": CALENDAR_TIMEZONE,
                                },
                                "end": {
                                    "date": second.strftime("%Y-%m-%d"),
                                    "timeZone": CALENDAR_TIMEZONE,
                                },
                            }
                            event_bodies.append(event_body)
                            idx += 2
                        else:
                            # 1つの独立した日付パターン
                            event_body = {
                                "summary": game_name,
                                "description": f"ゲームのURL: {url}",
                                "start": {
                                    "date": played_on.replace("/", "-"),
                                    "timeZone": CALENDAR_TIMEZONE,
                                },
                                "end": {
                                    "date": played_on.replace("/", "-"),
                                    "timeZone": CALENDAR_TIMEZONE,
                                },
                            }
                            event_bodies.append(event_body)
                            idx += 1
                    else:
                        # 1つの独立した日付パターン
                        event_body = {
                            "summary": game_name,
                            "description": f"ゲームのURL: {url}",
                            "start": {
                                "date": played_on.replace("/", "-"),
                                "timeZone": CALENDAR_TIMEZONE,
                            },
                            "end": {
                                "date": played_on.replace("/", "-"),
                                "timeZone": CALENDAR_TIMEZONE,
                            },
                        }
                        event_bodies.append(event_body)
                        idx += 1
        else:
            print(f"不正な played_ons: {played_ons}")
            sys.exit(1)

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
