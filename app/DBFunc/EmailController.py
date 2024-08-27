import imaplib
import email
from email.header import decode_header
from datetime import datetime
from app.extensions import db
from app.DBModels.EmailModel import Email
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("FROMEMAIL")
PASSWORD = os.getenv("PASSWORD")
SERVER = os.getenv("SERVER")
PORT = os.getenv("PORT")

class EmailController():

    def __init__(self):
        self.db = db
        self.Email = Email

    def check_inbox(self):
        mail = imaplib.IMAP4_SSL(SERVER, PORT)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        date = datetime(2024, 7, 1).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE {date})')
        email_ids = messages[0].split()

        for e_id in email_ids:
            status, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    sender = msg.get("From")
                    recipient = msg.get("To")

                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            try:
                                body = part.get_payload(decode=True).decode()
                            except:
                                pass
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                self.save_email(sender, recipient, body)
                    else:
                        content_type = msg.get_content_type()
                        body = msg.get_payload(decode=True).decode()
                        if content_type == "text/plain":
                            self.save_email(sender, recipient, body)

        mail.logout()


    def save_email(sender, recipient, body):
        email_entry = Email(sender=sender, recipient=recipient, message=body, date=datetime.now())
        db.session.add(email_entry)
        db.session.commit()


emailcontroller = EmailController()