import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

recipient = 'waichak.luk@gmail.com'
fromemail = 'wehamanagement@gmail.com'

def send_email( subject, body, html_content=None):
    msg = MIMEMultipart()
    msg['From'] = fromemail
    msg['To'] = recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if html_content:
        msg.attach(MIMEText(html_content, 'html'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(fromemail, 'ennyprrdtpvpxalh')
        text = msg.as_string()
        server.sendmail(fromemail, recipient, text)



# def send_email(listings):
#     # Placeholder for your email sending logic
#
#
#     try:
#         print("Attempting to send email...")
#
#         msg.attach(MIMEText(email_content, 'plain'))
#         with smtplib.SMTP('smtp.gmail.com', 587) as server:
#             server.starttls()
#             server.login("wehamanagement@gmail.com", "ennyprrdtpvpxalh")
#             text = msg.as_string()
#             print(text)
#             server.sendmail("wehamanagement@gmail.com", "waichak.luk@gmail.com", text)
#         print("Email sent!")
#     except Exception as e:
#         print(f"Error: {e}")