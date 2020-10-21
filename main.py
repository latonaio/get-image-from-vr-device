#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2019-2020 Latona. All rights reserved.

import os
import json
import cgi
import shutil
from pathlib import Path
from datetime import datetime,timedelta

from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server

from StatusJsonPythonModule import StatusJsonRest
from aion.logger_library.LoggerClient import LoggerClient

HOST = '0.0.0.0'
PORT = 8001
SAVEDIR = '/home/shinwa/luna/Data/get-image-from-vr-device/file/output'
UIDIR = '/home/shinwa/luna/UI/ui-backend-for-vr-face-recognition/public/uploads/vr_img'

log = LoggerClient("GetImageFromVrDevice")


def filedelete(target_dir):
    deltime = datetime.now() - timedelta(minutes=5)
    del_border = deltime.timestamp()

    path = Path(target_dir)
    for row in path.glob('*'):
        if del_border > row.stat().st_mtime:
            row.unlink()
        

class PostImageFile(object):
    
    def __init__(self):
        # read status json file
        self.statusObj = StatusJsonRest.StatusJsonRest(os.getcwd(), __file__)
        self.statusObj.initializeInputStatusJson()

        self.statusObj.initializeOutputStatusJson()
        self.statusObj.copyToOutputJsonFromInputJson()
        self.statusObj.setNextService(
            "FaceRecognitionFromImages",
            "/home/shinwa/luna/Runtime/face-recognition-from-images",
            "python", "main.py")
        """
        self.statusObj.setNextService(
            "ObjectDetectionFromImages",
            "/home/user/demeter/Runtime/object-detection-from-images",
            "python", "main.py", "workstation")
        """

        #shutil.rmtree(UIDIR)
        #os.mkdir(UIDIR)

        log.print(">>> start get image service")


    def __call__(self, environ, start_response):
        setup_testing_defaults(environ)

        status = '200 OK'
        headers = [
            ('Content-type', 'application/json; charset=utf-8'),
            ('Access-Control-Allow-Origin', '*'),
        ]

        start_response(status, headers)

        if environ['REQUEST_METHOD'] != 'POST':
            return ""

        form = cgi.FieldStorage(
            fp=environ['wsgi.input'],
            environ=environ,
            keep_blank_values=True
        )
        fileitem = form["image"]

        if fileitem.file:
            filename = fileitem.filename.encode('ascii').decode('utf8')
            filepath = os.path.join(SAVEDIR, filename)

            counter = 0
            with open(filepath, 'wb') as output_file:
                while 1:
                    data = fileitem.file.read(1024)
                    # End of file
                    if not data:
                        break
                    output_file.write(data)
                    counter += 1
                    if counter == 100:
                        counter = 0

            filedelete(UIDIR)
            uipath = os.path.join(UIDIR, filename)
            shutil.copy2(filepath, uipath)

            self.statusObj.setMetadataValue("filepath", filepath)
            self.statusObj.outputJsonFile()
            self.statusObj.resetOutputJsonFile()
            log.print("> Success: output json")

        return [json.dumps({'result':'success'}).encode("utf-8")]


def main():
    post_image_file = PostImageFile();

    with make_server(HOST, PORT, post_image_file) as httpd:
        # start req listning !!
        httpd.serve_forever()


if __name__ == "__main__":
    main()

