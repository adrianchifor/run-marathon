import os

import requests
from flask import Flask, make_response

app = Flask(__name__)


@app.route("/")
def index():
    if "SERVICE2_URL" in os.environ:
        jwt = get_auth_token(os.environ["SERVICE2_URL"])
        service2_response = requests.get(os.environ["SERVICE2_URL"],
                                         headers={"Authorization": f"bearer {jwt}"})
        return make_response(service2_response.content, 200)

    return make_response("service2 not found", 404)


def get_auth_token(receiving_service_url):
    token_request_url = ("http://metadata/computeMetadata/v1/instance/service-accounts"
        f"/default/identity?audience={receiving_service_url}")

    token_response = requests.get(token_request_url, headers={"Metadata-Flavor": "Google"})
    return token_response.content.decode("utf-8")