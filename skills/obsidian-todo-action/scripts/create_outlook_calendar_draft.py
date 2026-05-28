#!/usr/bin/env python3
import os
import datetime
import subprocess


def create_ics_draft(
    summary: str = "Meeting",
    description: str = "",
    location: str = "Microsoft Teams",
    start_dt: datetime.datetime = None,
    end_dt: datetime.datetime = None,
    attendees: list = None,
    output_filename: str = "meeting_draft.ics"
) -> str:
    """
    Creates an iCalendar (.ics) file that opens as an editable draft in Outlook.
    Omits ORGANIZER and METHOD:REQUEST so Outlook treats it as a local appointment.
    """
    if not start_dt:
        now = datetime.datetime.now()
        start_dt = (now + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    if not end_dt:
        end_dt = start_dt + datetime.timedelta(hours=1)

    dtstart_str = start_dt.strftime("%Y%m%dT%H%M%S")
    dtend_str = end_dt.strftime("%Y%m%dT%H%M%S")
    dtstamp_str = datetime.datetime.now().strftime("%Y%m%dT%H%M%SZ")

    escaped_description = description.replace("\r", "").replace("\n", "\\n")
    escaped_summary = summary.replace("\n", " ")
    escaped_location = location.replace("\n", " ")

    attendee_lines = ""
    if attendees:
        for a in attendees:
            name = a.get("name", "")
            email = a.get("email", "")
            if email:
                cn_part = f"CN={name};" if name else ""
                attendee_lines += f"ATTENDEE;{cn_part}RSVP=TRUE:mailto:{email}\r\n"

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Python//Outlook Draft Calendar Generator//EN
CALSCALE:GREGORIAN
BEGIN:VEVENT
UID:uid_{dtstamp_str}
DTSTAMP:{dtstamp_str}
DTSTART:{dtstart_str}
DTEND:{dtend_str}
SUMMARY:{escaped_summary}
DESCRIPTION:{escaped_description}
LOCATION:{escaped_location}
{attendee_lines}END:VEVENT
END:VCALENDAR
"""

    output_path = os.path.abspath(output_filename)
    with open(output_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(ics_content)

    print(f"[ics] Created: {output_path}")
    print("To open: double-click the file or right-click > Open With > Microsoft Outlook.")
    return output_path


def open_outlook_calendar_via_applescript(
    summary: str = "Meeting",
    description: str = "",
    location: str = "Microsoft Teams",
    hours_from_now: int = 1
) -> bool:
    """Uses macOS AppleScript to create and open a calendar event directly in Outlook."""
    now = datetime.datetime.now()
    start_dt = (now + datetime.timedelta(hours=hours_from_now)).replace(minute=0, second=0, microsecond=0)
    end_dt = start_dt + datetime.timedelta(hours=1)

    start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    escaped_body = description.replace('"', '\\"').replace('\n', '\\r')
    escaped_summary = summary.replace('"', '\\"')
    escaped_location = location.replace('"', '\\"')

    applescript_code = f'''
    tell application "Microsoft Outlook"
        activate
        set newEvent to make new calendar event with properties {{subject:"{escaped_summary}", plain text content:"{escaped_body}", location:"{escaped_location}", start time:date "{start_str}", end time:date "{end_str}"}}
        open newEvent
    end tell
    '''

    try:
        result = subprocess.run(['osascript', '-e', applescript_code], capture_output=True, text=True)
        if result.returncode == 0:
            print("Opened calendar event directly in Outlook via AppleScript.")
            return True
        else:
            print(f"AppleScript failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"Exception running AppleScript: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create an Outlook calendar invite draft (.ics)")
    parser.add_argument("--summary", required=True, help="Meeting title")
    parser.add_argument("--description", default="", help="Meeting agenda / description")
    parser.add_argument("--location", default="Microsoft Teams", help="Meeting location")
    parser.add_argument("--start", required=True,
                        help="Start datetime in ISO format: YYYY-MM-DDTHH:MM")
    parser.add_argument("--end", required=True,
                        help="End datetime in ISO format: YYYY-MM-DDTHH:MM")
    parser.add_argument("--attendee", action="append", default=[], metavar="NAME:EMAIL",
                        help="Attendee as 'Name:email@example.com' (repeat for multiple)")
    parser.add_argument("--output", required=True, help="Output .ics file path (absolute)")
    args = parser.parse_args()

    start_dt = datetime.datetime.fromisoformat(args.start)
    end_dt = datetime.datetime.fromisoformat(args.end)

    attendees = []
    for a in args.attendee:
        if ":" in a:
            name, email = a.split(":", 1)
            attendees.append({"name": name.strip(), "email": email.strip()})
        else:
            attendees.append({"name": "", "email": a.strip()})

    create_ics_draft(
        summary=args.summary,
        description=args.description,
        location=args.location,
        start_dt=start_dt,
        end_dt=end_dt,
        attendees=attendees,
        output_filename=args.output,
    )
