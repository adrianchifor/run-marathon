import os

import requestsgcp as requests
from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    if "SERVICE3_URL" in os.environ:
        service3_response = requests.get(os.environ["SERVICE3_URL"])
        return service3_response.content, 200

    return "service3 not found", 404
