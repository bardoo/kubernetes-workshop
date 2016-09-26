import socket
from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def index():
    log_param = request.args.get('log', None)
    if log_param:
        print("LOG: {}".format(log_param))

    return "Working! App v2.<br/>Intern IP: {}".format(get_ip())

@app.route('/ip')
def get_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(('8.8.8.8', 53))
    ip = sock.getsockname()[0]
    sock.close()

    return ip

@app.route('/kill-me')
def kill_app():
    exit(0)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000')
