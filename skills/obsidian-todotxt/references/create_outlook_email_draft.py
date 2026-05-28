#!/usr/bin/env python3
import os
import urllib.parse
import subprocess
import webbrowser
from email.message import EmailMessage

# ----------------------------------------------------------------------
# SOLUTION 1: Create an .emltpl File (Outlook for Mac Template format)
# ----------------------------------------------------------------------
def create_emltpl_file(
    from_addr: str = "test-sender@example.com",
    to_addr: str = "test-recipient@example.com",
    cc_addr: str = "test-cc@example.com",
    subject: str = "Test Outlook Template",
    body: str = "Hello,\n\nThis is an email draft template.\n\nBest regards,",
    output_filename: str = "draft_mail.emltpl"
) -> str:
    """
    Creates a standard .eml file structure but saves it with the .emltpl extension.
    Outlook for Mac treats .emltpl files as Email Templates which open in 
    a fully editable draft window.
    """
    msg = EmailMessage()
    msg['From'] = from_addr
    msg['To'] = to_addr
    if cc_addr:
        msg['Cc'] = cc_addr
    msg['Subject'] = subject
    msg.set_content(body)
    
    # Standard draft header for general clients
    msg['X-Unsent'] = '1'
    
    output_path = os.path.abspath(output_filename)
    with open(output_path, 'wb') as f:
        f.write(msg.as_bytes())
        
    print(f"[Method 1] .emltpl Template created at: {output_path}")
    print("👉 To open: Double-click this file or import it via 'File > New > Email From Template' in Outlook.")
    return output_path

# ----------------------------------------------------------------------
# SOLUTION 2: Use AppleScript via Python (Mac-Native Direct Draft Creation)
# ----------------------------------------------------------------------
def open_outlook_draft_via_applescript(
    to_addr: str = "test-recipient@example.com",
    cc_addr: str = "test-cc@example.com",
    subject: str = "Test AppleScript Draft",
    body: str = "Hello,\n\nThis was opened directly in Outlook via AppleScript.\n\nBest regards,"
) -> bool:
    """
    Uses macOS AppleScript to programmatically create and open an 
    editable draft message directly inside Microsoft Outlook for Mac.
    
    Note: Requires "Legacy Outlook" interface mode if using newer Outlook 
    versions where AppleScript API support might be limited.
    """
    # Build AppleScript command lines
    cc_script = ""
    if cc_addr:
        cc_script = f'make new recipient at newMsg with properties {{email address:{{address:"{cc_addr}"}}, recipient type:cc recipient}}'
        
    # Escape double quotes and newlines for AppleScript
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
        print("[Method 2] Triggering AppleScript to open draft directly in Outlook...")
        result = subprocess.run(['osascript', '-e', applescript_code], capture_output=True, text=True)
        if result.returncode == 0:
            print("👉 Success! An editable Outlook window has been opened.")
            return True
        else:
            print(f"❌ AppleScript failed: {result.stderr.strip()}")
            print("Note: AppleScript requires Outlook to be in Legacy mode on some macOS builds, and terminal permissions enabled.")
            return False
    except Exception as e:
        print(f"❌ Exception running AppleScript: {e}")
        return False

# ----------------------------------------------------------------------
# SOLUTION 3: Use mailto: URL Scheme (Lightweight & Cross-platform)
# ----------------------------------------------------------------------
def open_outlook_draft_via_mailto(
    to_addr: str = "test-recipient@example.com",
    cc_addr: str = "test-cc@example.com",
    subject: str = "Test Mailto Draft",
    body: str = "Hello,\n\nThis draft was opened using a system-level mailto URL.\n\nBest regards,"
) -> str:
    """
    Constructs a mailto URL and opens it using the system default handler.
    If Outlook is your default mail client, it opens a fully editable, 
    pre-populated draft instantly.
    
    Advantage: Zero external file requirements, cross-platform, and doesn't require 
    AppleScript automation permissions.
    """
    # Safe encoding for mailto parameters
    params = {
        'subject': subject,
        'body': body
    }
    if cc_addr:
        params['cc'] = cc_addr
        
    url_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    mailto_url = f"mailto:{to_addr}?{url_params}"
    
    print("[Method 3] Launching default email client using mailto URL...")
    webbrowser.open(mailto_url)
    print("👉 Success! The system's default mail client compose window should now be open.")
    return mailto_url

# ----------------------------------------------------------------------
# CLI/Test Execution
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    
    # Default test parameters
    default_from = "sender@example.com"
    default_to = "recipient@example.com"
    default_cc = "cc-recipient@example.com"
    default_subject = "Dynamic Draft Generation Test"
    default_body = "Hello User,\n\nThis email has been generated dynamically.\n\nThanks!\nPython Script"

    print("=== Outlook Mac Draft Generator ===")
    print("Outlook for Mac treats .eml files as read-only. Please choose a solution:")
    print("1) Generate an .emltpl file (Outlook Mac Template - fully editable)")
    print("2) Open directly in Outlook using AppleScript (No files, Mac-only)")
    print("3) Open via system-level 'mailto:' link (Zero permissions, cross-platform)")
    
    choice = input("\nEnter choice (1, 2, or 3) [Default: 1]: ").strip()
    if not choice:
        choice = "1"
        
    if choice == "1":
        create_emltpl_file(
            from_addr=default_from,
            to_addr=default_to,
            cc_addr=default_cc,
            subject=default_subject,
            body=default_body
        )
    elif choice == "2":
        open_outlook_draft_via_applescript(
            to_addr=default_to,
            cc_addr=default_cc,
            subject=default_subject,
            body=default_body
        )
    elif choice == "3":
        open_outlook_draft_via_mailto(
            to_addr=default_to,
            cc_addr=default_cc,
            subject=default_subject,
            body=default_body
        )
    else:
        print("Invalid choice. Exiting.")
