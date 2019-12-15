#!/usr/bin/env python3

import sys
import logging
import subprocess

from marathon.utils import get_marathon_config

log = logging.getLogger(__name__)


def get_user_email():
    user = None
    try:
        user, _ = eval_noout("gcloud config get-value account")
    except Exception:
        pass
    return user


def list():
    try:
        project = get_marathon_config()["project"]
        eval_stdout(f"gcloud run services list --platform=managed --project={project}")
    except Exception:
        log.debug("Could not get project from run.yaml, using gcloud default")
        eval_stdout("gcloud run services list --platform=managed")


def describe(service, region):
    if not region:
        try:
            region = get_marathon_config()["region"]
        except Exception:
            log.error(("Please specify a region, either in run.yaml or in "
                "'run describe <service> --region=<region>'"))
            return

    try:
        project = get_marathon_config()["project"]
        eval_stdout((f"gcloud run services describe {service} --platform=managed --region={region}"
            f" --project={project}"))
    except Exception:
        log.debug("Could not get project from run.yaml, using gcloud default")
        eval_stdout(f"gcloud run services describe {service} --platform=managed --region={region}")


def build(service, dir, image):
    project = get_marathon_config()["project"]
    eval_noout(f"gcloud builds submit --tag={image} {dir} --project={project}")


def deploy(service):
    project = get_marathon_config()["project"]
    default_region = get_marathon_config()["region"]
    service_conf = get_marathon_config()[service]
    # TODO: deploy


def eval_stdout(command):
    command = command.split(" ")
    try:
        proc = subprocess.Popen(command)
        proc.communicate()
    except FileNotFoundError:
        gcloud_not_installed()


def eval_noout(command):
    command = command.split(" ")
    try:
        pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = pipe.communicate()
        return (out.decode(), err.decode())
    except FileNotFoundError:
        gcloud_not_installed()


def gcloud_not_installed():
    log.error("gcloud not installed, please check https://cloud.google.com/sdk/install")
    sys.exit(1)
