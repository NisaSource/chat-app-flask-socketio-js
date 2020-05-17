import os
from ftplib import FTP

UPLOAD_FOLDER = f'{os.getcwd()}/static/upload'

channelsCreated = {"#general": []}
filenames = {}


def placeFile(filename):
    ftp = FTP('demo.wftpserver.com', timeout=400)
    ftp.login(user='demo-user', passwd='demo-user')
    ftp.cwd('/upload')
    ftp.storbinary(
        'STOR ' + filenames[filename], open(os.path.join(UPLOAD_FOLDER, filename), 'rb'))
    ftp.quit()


def get_channels():
    res = []
    for channel in channelsCreated.keys():
        res.append(channel)
    return res


def append_message(list, msg):
    if len(list) == 100:
        list.pop(0)
        list.append(msg)
    else:
        list.append(msg)
