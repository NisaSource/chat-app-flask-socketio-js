import os

import urllib.parse
import string
import random
from flask import Flask, jsonify, render_template, session, request, redirect
from flask_socketio import SocketIO, emit, send
from helper import get_channels, append_message, placeFile

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

UPLOAD_FOLDER = f'{os.getcwd()}/static/upload'

channelsCreated = {"#general": []}
usersLogged = {"#general": []}
usersTyping = {"#general": []}
channelsMessages = []
filenames = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/usercheck", methods=["POST"])
def usercheck():
    username = request.form.get("username")
    usernames = {"admin"}

    for channel in usersLogged.keys():
        for user in channel:
            usernames.add(user)

    print('usernames ', usernames)

    if username in usernames:
        return jsonify({"exists": True})
    else:
        return jsonify({"exists": False})


@socketio.on("type")
def on_type(msg):
    username = msg["username"]
    channel = msg["channel"]
    if msg["status"] == "end":
        if msg["username"] in usersTyping[msg["channel"]]:
            usersTyping[msg["channel"]].remove(msg["username"])

        message = {
            "usernames": usersTyping[channel],
            "channel": channel,
            "files": {}
        }

        emit("typing", message, broadcast=True)

    else:
        if channel not in usersTyping:
            usersTyping[channel] = []
        if username not in usersTyping[channel]:
            usersTyping[channel].append(username)

        message = {
            "usernames": usersTyping[channel],
            "channel": channel,
            "files": {}
        }

        emit("typing", message, broadcast=True)


@app.route("/send_file", methods=["POST"])
def send_file():
    file = request.files["file"]
    filename = file.filename
    filename = urllib.parse.unquote(filename)
    filename = ''.join(e for e in filename if e.isalnum() or e == ".")
    name, ext = os.path.splitext(filename)
    filenames[filename] = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for _ in range(20)) + ext
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    placeFile(filename)
    os.remove(os.path.join(UPLOAD_FOLDER, filename))
    return jsonify({"success": True})


@socketio.on("send message")
def msg_hndl(msg):
    print('msg===', msg)
    print('usersLogged===', usersLogged)
    if "connection" in msg and msg["username"] not in usersLogged[msg["channel"]] and not msg["username"] == None:
        message = {
            "connection": True,
            "text": "has connected",
            "username": msg["username"],
            "date": msg["date"],
            "channel": msg["channel"],
            "files": {}
        }
        usersLogged[msg["channel"]].append(msg["username"])
        append_message(channelsCreated[msg["channel"]], message)

        emit("announce message", {
             "messages": channelsCreated[msg["channel"]]}, broadcast=True)

    elif "connection" in msg and msg["username"] in usersLogged[msg["channel"]]:
        emit("announce message", {
             "messages": channelsCreated[msg["channel"]]})

    elif "connection" not in msg:
        files = {}

        for file in msg["files"]:
            file = ''.join(e for e in file if e.isalnum() or e == ".")

            files[file] = "http://flack-uploads-com.stackstaging.com/" + \
                filenames[file]

        message = {
            "connection": False,
            "text": msg["text"],
            "username": msg["username"],
            "date": msg["date"],
            "channel": msg["channel"],
            "files": files
        }
        print("channelsCreated=====", channelsCreated)
        print("msg['channel']====", msg["channel"])
        print("message", message)
        append_message(channelsCreated[msg["channel"]], message)

        emit("announce message", message, broadcast=True)


@socketio.on("add channel")
def add_channel(msg):
    if msg["channel"] not in channelsCreated:
        channelsCreated[msg["channel"]] = []
        usersLogged[msg["channel"]] = []
        emit("channel added", {"channel": msg["channel"]}, broadcast=True)


@socketio.on("get all channels")
def get_all_channels(msg):
    emit("channelsCreated", {"channelsCreated": get_channels()})


@socketio.on("get channel story")
def get_channel(msg):
    if msg["channel"] in channelsCreated:
        emit("announce message", {
             "messages": channelsCreated[msg["channel"]]})
    else:
        emit("announce message", {"messages": "#general"})


if __name__ == '__main__':
    socketio.run(app)
