#!/usr/bin/env python3
import os
import urllib.parse
import subprocess
import webbrowser
from email.message import EmailMessage


def create_emltpl_file(
    from_addr: str = "",
    to_addr: str = "recipient@example.com",
    cc_addr: str = "",
    subject: str = "Draft",
    body: str = "",
    output_filename: str = "draft_mail.emltpl"
) -> str:
    """
    Creates a standard .eml file structure saved with the .emltpl extension.
    Outlook for Mac treats .emltpl files as Email Templates which open in
    a fully editable draft window.
    """
    msg = EmailMessage()
    if from_addr:
        msg['From'] = from_addr
    msg['To'] = to_addr
    if cc_addr:
        msg['Cc'] = cc_addr
    msg['Subject'] = subject
    msg.set_content(body)
    msg['X-Unsent'] = '1'

    output_path = os.path.abspath(output_filename)
    with open(output_path, 'wb') as f:
        f.write(msg.as_bytes())

    print(f"[emltpl] Created: {output_path}")
    print("To open: double-click the file, or File > New > Email From Template in Outlook.")
    return output_path


def open_outlook_draft_via_applescript(
    to_addr: str = "recipient@example.com",
    cc_addr: str = "",
    subject: str = "Draft",
    body: str = ""
) -> bool:
    """Uses macOS AppleScript to open an editable draft directly in Outlook."""
    cc_script = ""
    if cc_addr:
        cc_script = f'make new recipient at newMsg with properties {{email address:{{address:"{cc_addr}"}}, recipient type:cc recipient}}'

    escaped_body = body.replace('"', '\\"').replace('\n', '\\r')
    escaped_subject = subject.replace('"', '\\"')

    applescript_code = f'''
    tell application "Microsoft Outlook"
        activate
        set newMsg to make new outgoing message with properties {{subject:"{escaped_subject}", plain text content:"{escaped_body}"}}
        make new recipient at newMsg with properties {{email address:{{address:"{to_addr}"}}, recipient type:to recipient}}
        {cc_script}
        open newMsg
    end tell
    '''

    try:
        result = subprocess.run(['osascript', '-e', applescript_code], capture_output=True, text=True)
        if result.returncode == 0:
            print("Opened draft directly in Outlook via AppleScript.")
            return True
        else:
            print(f"AppleScript failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"Exception running AppleScript: {e}")
        return False


def open_outlook_draft_via_mailto(
    to_addr: str = "recipient@example.com",
    cc_addr: str = "",
    subject: str = "Draft",
    body: str = ""
) -> str:
    """Opens a mailto: URL in the system default mail client."""
    params = {'subject': subject, 'body': body}
    if cc_addr:
        params['cc'] = cc_addr
    url_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    mailto_url = f"mailto:{to_addr}?{url_params}"
    webbrowser.open(mailto_url)
    print("Launched default email client via mailto URL.")
    return mailto_url


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create an Outlook email draft (.emltpl)")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--from", dest="from_addr", default="",
                        help="Sender address (leave blank for Outlook default account)")
    parser.add_argument("--cc", default="", help="CC email address")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--body", required=True, help="Email body text")
    parser.add_argument("--output", required=True, help="Output .emltpl file path (absolute)")
    args = parser.parse_args()

    create_emltpl_file(
        from_addr=args.from_addr,
        to_addr=args.to,
        cc_addr=args.cc,
        subject=args.subject,
        body=args.body,
        output_filename=args.output,
    )
