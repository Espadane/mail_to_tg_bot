import os
import base64
import imaplib
import logging
from datetime import datetime
from email.parser import BytesParser
from email import policy
from dotenv import load_dotenv


class EmailClient:
    def __init__(self, imap_address: str,
                    email_login: str,
                    email_password: str) -> None:
        """
        Инициализация клиента электронной почты.

        Args:
            imap_address (str): Адрес IMAP-сервера.
            email_login (str): Логин электронной почты.
            email_password (str): Пароль электронной почты.
        """
        self.imap_address = imap_address
        self.email_login = email_login
        self.email_password = email_password
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger_handler = logging.FileHandler('email_client.log', encoding='utf-8')
        self.logger_formatter = logging.Formatter(f'%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s', 
                                                  datefmt='%d.%b.%Y %H:%M')
        self.logger.addHandler(self.logger_handler)
        self.logger_handler.setFormatter(self.logger_formatter)
        
        if not os.path.exists('./attach/'):
            os.mkdir('./attach/')
            self.logger.debug("Папка attach создана.")
        if not os.path.exists('./confirmed_users.txt'):
            with open('./confirmed_users.txt', 'w', encoding='utf-8') as file:
                pass
                self.logger.debug("Файл confirmed_users.txt создан.")
                
            
    def connect(self) -> None:
        """
        Установление соединения с почтовым сервером.
        """
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_address)
            self.mail.login(self.email_login, self.email_password)
            self.mail.select('inbox')
            self.logger.debug('Подключено к серверу электронной почты.')
        except Exception as e:
            self.logger.warning(f"Подключение к серверу электронной почты не произошло: \n{e}")
            
    def disconnect(self) -> None:
        """
        Закрытие соединения с почтовым сервером.
        """
        try:
            self.mail.logout()
            self.logger.debug("Соединение с почтовым сервером закрыто.")
        except Exception as e:
            self.logger.warning(f"Ошибка закрытие соединения с почтовым сервером: \n{e}")
            
    def get_messages(self) -> list:
        """
        Получение новых сообщений.

        Returns:
            list: Список словарей с данными о сообщениях.
        """
        now_date = datetime.now().strftime("%H%M%S_%d%m%Y")
        status, messages = self.mail.search(None, '(UNSEEN)')
        message_ids = messages[0].split()
        mails = []
        
        for msg_id in message_ids:
            try:
                status, msg_data = self.mail.fetch(msg_id, '(RFC822)')
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
                    try:
                        text = base64.b64decode(text).decode('cp1251').strip()
                    except Exception as e:
                        self.logger.warning(f'Failed to decode the message body: {e}')
                        
                mails.append({
                    'mail_subject': subject,
                    'mail_text': text,
                    'mail_attachments': mail_attachments,
                    'now_date': now_date
                })
                self.logger.debug(f'Сообщение с темой "{subject}" получено успешно.')
            except Exception as e:
                self.logger.warning(f'Ошибка получения сообщений: \n{e}')
                
        return mails


def process_messages():
    load_dotenv()
    
    client = EmailClient(
        imap_address=os.getenv("IMAP_ADDRESS"),
        email_login=os.getenv("EMAIL_LOGIN"),
        email_password=os.getenv("EMAIL_PASSWORD")
    )
    
    client.connect()
    mails = client.get_messages()
    client.disconnect()
    
    return mails