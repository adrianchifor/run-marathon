import os

import requestsgcp as requests
from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    if "SERVICE2_URL" in os.environ:
        service2_response = requests.get(os.environ["SERVICE2_URL"])
        return service2_response.content, 200

    return "service2 not found", 404
