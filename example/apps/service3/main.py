from flask import Flask, make_response

app = Flask(__name__)


@app.route("/")
def index():
    return make_response("Hello from service3", 200)
