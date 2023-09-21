import os
import base64
import imaplib
from datetime import datetime
from email.parser import BytesParser
from email import policy
from dotenv import load_dotenv


if not os.path.exists('./attach/'):
    os.mkdir('./attach/')

async def get_mails():
    load_dotenv()
    now_date = datetime.now().strftime("%H%M%S_%d%m%Y")
    mail = imaplib.IMAP4_SSL(os.getenv("IMAP_ADDRESS"))
    mail.login(os.getenv("EMAIL_LOGIN"), os.getenv("EMAIL_PASSWORD"))
    mail.select('inbox')
    status, messages = mail.search(None, '(UNSEEN)')
    message_ids = messages[0].split()
    mails = []
    for msg_id in message_ids:
        status, msg_data = mail.fetch(msg_id, '(RFC822)')
        msg_bytes = msg_data[0][1]

        msg = BytesParser(policy=policy.default).parsebytes(msg_bytes)
        subject = msg['subject']
        text = ""
        attachments = []
        mail_attachments = []
        
        if msg.is_multipart():
            if not os.path.exists(f"./attach/{now_date}"):
                os.mkdir(f'./attach/{now_date}')
            for part in msg.iter_parts():
                content_disposition = part.get("Content-Disposition", None)

                if content_disposition and "attachment" in content_disposition:
                    filename = part.get_filename()
                    attachments.append((filename, part.get_payload(decode=True)))
                    with open(f"./attach/{now_date}/{filename}", "wb") as file:
                        file.write(part.get_payload(decode=True))
                        mail_attachments.append(filename)
                elif part.get_content_type() == "text/plain":
                    text = part.get_payload()
        else:
            text = msg.get_payload()
        try:
            text = base64.b64decode(text).decode('utf-8').strip()
        except UnicodeDecodeError:
            text = text.strip()
            
        mails.append(
            {
            'mail_subject' : subject,
            'mail_text' : text,
            'mail_attachments': mail_attachments,
            'now_date' : now_date}
        )

    mail.logout()
    
    return mails