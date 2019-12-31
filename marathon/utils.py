#!/usr/bin/env python3

import re
import logging
import yaml

import marathon.cached as cached

log = logging.getLogger(__name__)

VAR_REGEX = re.compile("\${(.*?)}")


def get_marathon_config():
    if not cached.marathon_config:
        with open("run.yaml", "r") as f:
            cached.marathon_config = yaml.safe_load(f)

    return cached.marathon_config


def init_marathon_config():
    return {
        "project": "your_project",
        "region": "your_default_region",
        "allow-invoke": [
            "user:your_user@domain.com"
        ],

        "service1": {
            "image": "gcr.io/${project}/service1:latest",
            "dir": "apps/service1",
            "authenticated": "false",
            "concurrency": "30",
            "links": [
                "service2"
            ],
        },

        "service2": {
            "image": "gcr.io/${project}/service2:latest",
            "dir": "apps/service2",
            "links": [
                "service3"
            ],
        },

        "service3": {
            "image": "gcr.io/${project}/service3:latest",
            "dir": "apps/service3",
            "cron": {
                "schedule": "0 * * * *",
                "http-method": "get",
            },
        },
    }


def interpolate_var(string):
    interpolated_string = str(string)
    for match in set(re.findall(VAR_REGEX, str(string))):
        try:
            match_interpolation = get_marathon_config()[match]
            interpolated_string = string.replace("${{{}}}".format(match), match_interpolation)
        except KeyError:
            log.error(f"Failed to interpolate {string} in run.yaml")

    return interpolated_string


def service_iter():
    for service in get_marathon_config().keys():
        if service != "project" and service != "region" and service != "allow-invoke":
            yield service


def service_dependencies():
    deps_map = {}
    nodeps_list = []
    conf = get_marathon_config()
    for service in service_iter():
        if "links" in conf[service] and len(conf[service]["links"]) > 0:
            deps_map[service] = set(conf[service]["links"])
        else:
            nodeps_list.append(service)

    return deps_map, nodeps_list


def sanitize_service_name(service):
    return service.lower().replace("_", "-")
