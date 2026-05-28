#!/usr/bin/env python3
import os
import datetime
import subprocess

# ----------------------------------------------------------------------
# SOLUTION 1: Create an Editable .ics File (iCalendar Draft)
# ----------------------------------------------------------------------
def create_ics_draft(
    summary: str = "Project Sync Meeting",
    description: str = "Hi Team,\n\nLet's catch up to discuss the project roadmap.\n\nBest,",
    location: str = "Conference Room A / Microsoft Teams",
    start_dt: datetime.datetime = None,
    end_dt: datetime.datetime = None,
    attendees: list = None,   # list of dicts: [{"name": "Alice", "email": "alice@example.com"}, ...]
    output_filename: str = "meeting_draft.ics"
) -> str:
    """
    Creates an iCalendar (.ics) file designed to open as an editable draft/event 
    in Outlook. By omitting the 'METHOD:REQUEST' and 'ORGANIZER' tags, Outlook 
    treats the event as a local personal appointment upon opening. 
    
    The user can then modify details, add attendees, and click 'Save & Close' 
    or 'Send' to dispatch meeting invitations.
    """
    # Use default times (Next hour) if not specified
    if not start_dt:
        now = datetime.datetime.now()
        start_dt = (now + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    if not end_dt:
        end_dt = start_dt + datetime.timedelta(hours=1)
        
    # Format times in ICS iCalendar format (e.g., YYYYMMDDTHHMMSS)
    # Using local times (without 'Z') so it defaults to the user's current timezone
    dtstart_str = start_dt.strftime("%Y%m%dT%H%M%S")
    dtend_str = end_dt.strftime("%Y%m%dT%H%M%S")
    dtstamp_str = datetime.datetime.now().strftime("%Y%m%dT%H%M%SZ")
    
    # We escape newlines in the description according to RFC 5545 (\n)
    escaped_description = description.replace("\r", "").replace("\n", "\\n")
    escaped_summary = summary.replace("\n", " ")
    escaped_location = location.replace("\n", " ")
    
    # Build ATTENDEE lines (RFC 5545)
    attendee_lines = ""
    if attendees:
        for a in attendees:
            name = a.get("name", "")
            email = a.get("email", "")
            if email:
                cn_part = f"CN={name};" if name else ""
                attendee_lines += f"ATTENDEE;{cn_part}RSVP=TRUE:mailto:{email}\r\n"

    # Construct the iCalendar content
    # Note: We omit ORGANIZER and METHOD:REQUEST to keep it fully editable
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
        
    print(f"[Method 1] Editable .ics file created at: {output_path}")
    print("👉 To open: Double-click this file or right-click -> Open With -> Microsoft Outlook.")
    return output_path

# ----------------------------------------------------------------------
# SOLUTION 2: Use AppleScript via Python (Mac-Native Direct Event Creation)
# ----------------------------------------------------------------------
def open_outlook_calendar_via_applescript(
    summary: str = "Project Sync Meeting",
    description: str = "Hi Team,\n\nLet's catch up to discuss the project roadmap.\n\nBest,",
    location: str = "Conference Room A",
    hours_from_now: int = 1
) -> bool:
    """
    Uses macOS AppleScript to create a calendar event directly in Outlook's 
    database and immediately opens its inspector window for editing.
    """
    # Calculate starting/ending dates
    now = datetime.datetime.now()
    start_dt = (now + datetime.timedelta(hours=hours_from_now)).replace(minute=0, second=0, microsecond=0)
    end_dt = start_dt + datetime.timedelta(hours=1)
    
    # Format dates into a style AppleScript's 'date' command reliably parses on Mac
    # System locale can vary, but standard ISO YYYY-MM-DD HH:MM:SS is highly compatible
    start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # Escape quotes and clean newlines for AppleScript string syntax
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
        print("[Method 2] Triggering AppleScript to create and open calendar event directly...")
        result = subprocess.run(['osascript', '-e', applescript_code], capture_output=True, text=True)
        if result.returncode == 0:
            print("👉 Success! An editable Outlook Calendar Event window has been opened.")
            return True
        else:
            print(f"❌ AppleScript failed: {result.stderr.strip()}")
            print("Note: AppleScript requires Outlook to be in Legacy mode on some macOS builds, and terminal permissions enabled.")
            return False
    except Exception as e:
        print(f"❌ Exception running AppleScript: {e}")
        return False


# ----------------------------------------------------------------------
# CLI/Test Execution
# ----------------------------------------------------------------------
if __name__ == "__main__":
    default_summary = "Product Roadmap Alignment"
    default_desc = "Let's review the milestones and align on the launch date.\n\nDraft invitation generated via Python."
    default_loc = "Microsoft Teams Meeting"
    
    print("=== Outlook Mac Calendar Event Draft Generator ===")
    print("Please choose a method to create an editable calendar event:")
    print("1) Generate an editable .ics file (No ORGANIZER/METHOD - opens as editable)")
    print("2) Open directly in Outlook using AppleScript (Mac-only)")
    
    choice = input("\nEnter choice (1 or 2) [Default: 1]: ").strip()
    if not choice:
        choice = "1"
        
    if choice == "1":
        create_ics_draft(
            summary=default_summary,
            description=default_desc,
            location=default_loc
        )
    elif choice == "2":
        open_outlook_calendar_via_applescript(
            summary=default_summary,
            description=default_desc,
            location=default_loc
        )
    else:
        print("Invalid choice. Exiting.")
