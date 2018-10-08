#!/usr/bin/env python
# -*- coding: utf-8 -*-

import httplib2
import os
import io

from apiclient import discovery
from oauth2client import client, tools
from oauth2client.file import Storage
from googleapiclient.http import MediaIoBaseDownload

CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'fb2mobi'
SCOPES = 'https://www.googleapis.com/auth/drive.readonly'


class GoogleDrive():
    def __init__(self, credential_file, executable_path):
        self.credential_file = credential_file
        self.executable_path = executable_path

        self.http = httplib2.Http(ca_certs=os.path.join(self.executable_path, 'cacerts.txt'))
        credentials = self.get_credentials()
        self.http = credentials.authorize(self.http)
        self.service = discovery.build('drive', 'v3', http=self.http)

    def list(self, dir_id):
        result = self.service.files().list(
            q="'{0}' in parents and trashed=false".format(dir_id),
            orderBy='folder,name',
            fields='nextPageToken, files(id, name, mimeType)'
            ).execute()

        items = result.get('files', [])
        return items

    def get_credentials(self):
        credential_dir = os.path.split(self.credential_file)[0]
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)

        store = Storage(self.credential_file)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(os.path.join(self.executable_path, CLIENT_SECRET_FILE), SCOPES)
            flow.user_agent = APPLICATION_NAME           
            credentials = tools.run_flow(flow, store, http=self.http)

        return credentials

    def download(self, file_id, path):
        if not os.path.exists(path):
            os.makedirs(path)

        request = self.service.files().get_media(fileId=file_id)
        name = self.service.files().get(fileId=file_id).execute()['name']

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        file_name = os.path.join(path, name)
        f = open(file_name, 'wb')
        f.write(fh.getvalue())

        return file_name




        
