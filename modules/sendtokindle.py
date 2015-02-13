#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
CLI tool for sending files via email to your Kindle device.
You need to have a working IMAP account.

This script is originally based on:
http://rakesh.fedorapeople.org/misc/pykindle.py (Public Domain)

Author: Kamil Páral <kamil.paral /at/ gmail.com>
'''
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import getpass
import os
import smtplib
import sys
import traceback
from StringIO import StringIO
from email import encoders
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.generator import Generator

_version = '2.1'


class SendKindle:
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
        '''Send email with attachments'''

        # create MIME message
        msg = MIMEMultipart()
        msg['From'] = self.user_email
        msg['To'] = self.kindle_email
        msg['Subject'] = 'Convert' if self.convert else 'Sent to Kindle'
        text = 'This email has been automatically sent by SendKindle tool.'
        msg.attach(MIMEText(text))

        # attach files
        for file_path in self.files:
            msg.attach(self.get_attachment(file_path))

        # convert MIME message to string
        fp = StringIO()
        gen = Generator(fp, mangle_from_=False)
        gen.flatten(msg)
        msg = fp.getvalue()

        # send email
        try:
            mail_server = smtplib.SMTP_SSL(host=self.smtp_server,
                                          port=self.smtp_port)
            mail_server.login(self.smtp_login, self.smtp_password)
            mail_server.sendmail(self.user_email, self.kindle_email, msg)
            mail_server.close()
        except smtplib.SMTPException as e:
            traceback.print_exc()
            message = ('Communication with your SMTP server failed. Maybe '
                       'wrong connection details? Check exception details and '
                       'your config file: %s' % self.conffile)
            print >> sys.stderr, message
            sys.exit(7)

    def get_attachment(self, file_path):
        '''Get file as MIMEBase message'''

        try:
            file_ = open(file_path, 'rb')
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(file_.read())
            file_.close()
            encoders.encode_base64(attachment)

            attachment.add_header('Content-Disposition', 'attachment',
                                  filename=os.path.basename(file_path))
            return attachment
        except IOError:
            traceback.print_exc()
            message = ('The requested file could not be read. Maybe wrong '
                       'permissions?')
            print >> sys.stderr, message
            sys.exit(6)


