# -*- coding: utf-8 -*-

import os

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart


class SendToKindle:
    def __init__(self):
        self.smtp_server = None
        self.smtp_port = 0
        self.smtp_login = None
        self.user_email = None
        self.kindle_email = None
        self.smtp_password = None
        self.convert = False

        self.parser = None
        self.files = []

    def send_mail(self):
        msg = MIMEMultipart()
        msg['From'] = self.user_email
        msg['To'] = self.kindle_email
        msg['Subject'] = 'Convert' if self.convert else 'Sent to Kindle'
        msg.preamble = 'This email has been automatically sent by fb2mobi tool'

        for file_path in self.files:
            fname = os.path.basename(file_path)
            msg.attach(MIMEApplication(open(file_path, 'rb').read(), Content_Disposition='attachment; filename="%s"' % fname, Name=fname))

        mail_server = smtplib.SMTP(host=self.smtp_server, port=self.smtp_port)
        mail_server.starttls()
        mail_server.login(self.smtp_login, self.smtp_password)
        mail_server.sendmail(self.user_email, self.kindle_email, msg.as_string())
        mail_server.quit()
