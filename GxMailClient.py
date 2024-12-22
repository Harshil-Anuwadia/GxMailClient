import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from colorama import Fore, Style, init
import os
import re
import json
import time
import logging

# Initialize colorama for colored output
init(autoreset=True)

# Set up logging
logging.basicConfig(filename='email_client.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# SMTP Server Configuration
SMTP_SERVER = 'Your SMTP Address'
SMTP_PORT = 587
USERNAME = 'Your Username'  # Update with your username
PASSWORD = 'Your Password'  # Update with your actual password
SENDER_EMAIL = 'Your Email ID'  # Sender's email address
DRAFT_FILE = 'drafts.json'  # File to store drafts
SENT_FILE = 'sent.json'  # File to store sent emails

# Predefined templates for quick email creation
TEMPLATES = {
    "Meeting Request": "Hi, I would like to schedule a meeting at your earliest convenience. Please let me know your availability.",
    "Thank You": "Thank you for your time and consideration. I look forward to hearing from you soon.",
    "Job Application": "Dear Hiring Manager, I am applying for the position of {position}. I have attached my resume and cover letter for your review."
}

# Signature for emails
SIGNATURE = "\n\nBest Regards,\nHarshil Anuwadia"

def validate_email(email):
    """Check if the email is valid using a regular expression."""
    email_regex = re.compile(r"[^@]+@[^@]+\.[^@]+")
    return email_regex.match(email) is not None

def save_draft(draft):
    """Save draft email to a JSON file."""
    try:
        drafts = load_drafts()  # Load existing drafts
        drafts.append(draft)
        with open(DRAFT_FILE, 'w') as f:
            json.dump(drafts, f, indent=4)
        print(f"{Fore.YELLOW}Draft saved successfully.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error saving draft: {e}{Style.RESET_ALL}")
        logging.error(f"Error saving draft: {e}")

def load_drafts():
    """Load and display saved drafts."""
    try:
        if os.path.exists(DRAFT_FILE):
            with open(DRAFT_FILE, 'r') as f:
                drafts = json.load(f)
            return drafts
        else:
            return []
    except Exception as e:
        print(f"{Fore.RED}Error loading drafts: {e}{Style.RESET_ALL}")
        logging.error(f"Error loading drafts: {e}")
        return []

def save_sent_email(email_data):
    """Save sent email data to a JSON file."""
    try:
        sent_emails = load_sent_emails()  # Load existing sent emails
        sent_emails.append(email_data)
        with open(SENT_FILE, 'w') as f:
            json.dump(sent_emails, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving sent email: {e}")

def load_sent_emails():
    """Load and display sent emails."""
    try:
        if os.path.exists(SENT_FILE):
            with open(SENT_FILE, 'r') as f:
                sent_emails = json.load(f)
            return sent_emails
        else:
            return []
    except Exception as e:
        print(f"{Fore.RED}Error loading sent emails: {e}{Style.RESET_ALL}")
        logging.error(f"Error loading sent emails: {e}")
        return []

def send_email(sender_email, display_name, receiver_emails, subject, body, priority, cc_emails=None, bcc_emails=None, read_receipt=False):
    retries = 3  # Number of automatic retries
    for attempt in range(retries):
        try:
            # Setting up the MIME
            message = MIMEMultipart()
            message['From'] = f"{display_name} <{sender_email}>"
            message['To'] = ', '.join(receiver_emails)
            message['Subject'] = subject
            message['X-Priority'] = str(priority)

            if cc_emails:
                message['Cc'] = ', '.join(cc_emails)

            # Attach the email body with signature
            full_body = f"{body.strip()}\n\n{SIGNATURE.strip()}"
            message.attach(MIMEText(full_body, 'plain'))

            # Request read receipt if chosen
            if read_receipt:
                message['Disposition-Notification-To'] = sender_email

            # Establish connection to the SMTP server
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(USERNAME, PASSWORD)

            # Send the email
            recipients = receiver_emails + (cc_emails if cc_emails else []) + (bcc_emails if bcc_emails else [])
            server.sendmail(sender_email, recipients, message.as_string())
            server.quit()

            print(f"{Fore.GREEN}Email sent successfully to {', '.join(receiver_emails)}{Style.RESET_ALL}")
            logging.info(f"Email sent successfully to {', '.join(receiver_emails)}")
            save_sent_email({
                "receiver_emails": receiver_emails,
                "cc_emails": cc_emails,
                "bcc_emails": bcc_emails,
                "subject": subject,
                "body": body,
                "priority": priority,
                "timestamp": time.time()
            })
            break

        except smtplib.SMTPAuthenticationError:
            print(f"{Fore.RED}Error: Authentication failed. Check your SMTP credentials.{Style.RESET_ALL}")
            logging.error("Authentication failed.")
            break
        except smtplib.SMTPRecipientsRefused:
            print(f"{Fore.RED}Error: The email was refused by one or more recipients.{Style.RESET_ALL}")
            logging.error("Email refused by recipients.")
            break
        except Exception as e:
            print(f"{Fore.RED}Failed to send email on attempt {attempt + 1}/{retries}: {e}{Style.RESET_ALL}")
            logging.error(f"Failed to send email on attempt {attempt + 1}: {e}")
            if attempt + 1 < retries:
                print(f"{Fore.YELLOW}Retrying...{Style.RESET_ALL}")
                time.sleep(2)  # Wait for 2 seconds before retrying
            else:
                print(f"{Fore.RED}All retries failed. Saving email as a draft.{Style.RESET_ALL}")
                save_draft({
                    "receiver_emails": receiver_emails,
                    "cc_emails": cc_emails,
                    "bcc_emails": bcc_emails,
                    "subject": subject,
                    "body": body,
                    "priority": priority
                })
                break

def get_emails(prompt):
    """Helper function to get and validate email addresses."""
    while True:
        emails = input(prompt).strip()
        if emails.lower() == 'exit':
            return None
        if emails == "":  # Allow skipping
            return []  # Return an empty list for skipped fields
        email_list = [email.strip() for email in emails.split(',')]
        invalid_emails = [email for email in email_list if not validate_email(email)]
        if invalid_emails:
            print(f"{Fore.RED}Error: Invalid email address(es) - {', '.join(invalid_emails)}{Style.RESET_ALL}")
            logging.warning(f"Invalid email address(es) entered: {', '.join(invalid_emails)}")
        else:
            return email_list

def input_with_default(prompt, default):
    """Helper function to show prompt with default value option."""
    user_input = input(f"{prompt} [{default}]: ").strip()
    return user_input if user_input else default

def preview_email(receiver_emails, cc_emails, bcc_emails, subject, body):
    """Display a preview of the email."""
    print(f"\n{Fore.CYAN}--- Email Preview ---{Style.RESET_ALL}")
    print(f"To: {', '.join(receiver_emails)}")
    if cc_emails:
        print(f"CC: {', '.join(cc_emails)}")
    if bcc_emails:
        print(f"BCC: {', '.join(bcc_emails)}")
    print(f"Subject: {subject}")
    print(f"Body:\n{body.strip()}\n{SIGNATURE.strip()}\n")  # Remove extra indentation
    print(f"{Fore.YELLOW}--- End of Preview ---{Style.RESET_ALL}")

def setup_signature():
    """Set up or change the email signature."""
    global SIGNATURE
    new_signature = input("Enter your new signature: ")
    SIGNATURE = new_signature.strip()
    print(f"{Fore.GREEN}Signature updated successfully.{Style.RESET_ALL}")

def main():
    global SENDER_EMAIL  # Ensure SENDER_EMAIL is in global scope
    print(f"{Fore.CYAN}Welcome to the Enhanced Professional Email Client CLI{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Tip: Type 'exit' to cancel at any time.{Style.RESET_ALL}")

    while True:
        action = input(f"{Fore.YELLOW}Choose action: 1) Compose Email 2) View Drafts 3) Use Template 4) Set Up Signature 5) View Sent Emails 6) Exit: {Style.RESET_ALL}").strip()

        if action == '1':  # Compose new email
            display_name = input("Enter your display name: ")
            receiver_emails = get_emails("Enter recipient(s) email address (comma-separated for multiple): ")
            if receiver_emails is None: break

            cc_emails = get_emails("Enter CC email addresses (comma-separated, or press Enter to skip): ")
            if cc_emails is None: cc_emails = []

            bcc_emails = get_emails("Enter BCC email addresses (comma-separated, or press Enter to skip): ")
            if bcc_emails is None: bcc_emails = []

            subject = input("Enter the subject of the email: ")
            if subject.lower() == 'exit': break
            body = input("Enter the body of the email: ")
            if body.lower() == 'exit': break

            priority = input("Enter the priority (1 = High, 3 = Normal, 5 = Low): ")
            priority = int(priority) if priority.isdigit() else 3  # Default to Normal if invalid
            read_receipt = input("Request a read receipt? (yes/no): ").strip().lower() == 'yes'

            # Preview the email before sending
            preview_email(receiver_emails, cc_emails, bcc_emails, subject, body)
            send = input("Do you want to send this email? (yes/no): ").strip().lower()

            if send == 'yes':
                send_email(SENDER_EMAIL, display_name, receiver_emails, subject, body, priority, cc_emails, bcc_emails, read_receipt=read_receipt)

        elif action == '2':  # View drafts
            drafts = load_drafts()
            if drafts:
                print(f"{Fore.CYAN}--- Drafts ---{Style.RESET_ALL}")
                for idx, draft in enumerate(drafts, start=1):
                    print(f"{idx}) To: {', '.join(draft['receiver_emails'])}, Subject: {draft['subject']}")
                print(f"{Fore.YELLOW}--- End of Drafts ---{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}No drafts available.{Style.RESET_ALL}")

        elif action == '3':  # Use template
            print(f"{Fore.CYAN}Available templates: {', '.join(TEMPLATES.keys())}{Style.RESET_ALL}")
            template_choice = input("Enter template name (or 'exit' to cancel): ").strip()
            if template_choice.lower() == 'exit': break
            if template_choice in TEMPLATES:
                subject = input("Enter the subject of the email: ")
                body = TEMPLATES[template_choice]
                display_name = input("Enter your display name: ")
                receiver_emails = get_emails("Enter recipient(s) email address (comma-separated for multiple): ")
                if receiver_emails is None: break
                cc_emails = get_emails("Enter CC email addresses (comma-separated, or press Enter to skip): ")
                if cc_emails is None: cc_emails = []
                bcc_emails = get_emails("Enter BCC email addresses (comma-separated, or press Enter to skip): ")
                if bcc_emails is None: bcc_emails = []

                preview_email(receiver_emails, cc_emails, bcc_emails, subject, body)
                send = input("Do you want to send this email? (yes/no): ").strip().lower()
                if send == 'yes':
                    send_email(SENDER_EMAIL, display_name, receiver_emails, subject, body, 3, cc_emails, bcc_emails)

            else:
                print(f"{Fore.RED}Template not found.{Style.RESET_ALL}")

        elif action == '4':  # Set up signature
            setup_signature()

        elif action == '5':  # View sent emails
            sent_emails = load_sent_emails()
            if sent_emails:
                print(f"{Fore.CYAN}--- Sent Emails ---{Style.RESET_ALL}")
                for idx, email in enumerate(sent_emails, start=1):
                    print(f"{idx}) To: {', '.join(email['receiver_emails'])}, Subject: {email['subject']}, Sent at: {time.ctime(email['timestamp'])}")
                print(f"{Fore.YELLOW}--- End of Sent Emails ---{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}No sent emails available.{Style.RESET_ALL}")

        elif action == '6':  # Exit
            confirm_exit = input("Are you sure you want to exit? (yes/no): ").strip().lower()
            if confirm_exit == 'yes':
                print(f"{Fore.GREEN}Exiting the email client. Goodbye!{Style.RESET_ALL}")
                break

        else:
            print(f"{Fore.RED}Invalid option. Please try again.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()