#!/usr/bin/env python

import requests
import json
import yaml
import os

# User Variables
username = "admin"
password = "Arista123"
server1 = "https://192.168.255.50"
image_name = "EOS-4.23.4M.swi"
terminattr = "TerminAttr-1.9.6-1.swix"
containers_to_build = ["Leaf", "Spine", "MGMT-ToR", "MGMT-Spine"]

# Do not modify anything below this line. Or do, I'm not a cop.
connect_timeout = 10
headers = {"Accept": "application/json", "Content-Type": "application/json"}
requests.packages.urllib3.disable_warnings()
session = requests.Session()


def login(url_prefix, username, password):
    auth_data = {"userId": username, "password": password}
    headers.pop("APP_SESSION_ID", None)
    response = session.post(
        f"{url_prefix}/web/login/authenticate.do",
        data=json.dumps(auth_data),
        headers=headers,
        timeout=connect_timeout,
        verify=False,
    )
    cookies = response.cookies
    headers["APP_SESSION_ID"] = response.json()["sessionId"]
    if response.json()["sessionId"]:
        return response.json()["sessionId"]


def logout(url_prefix):
    response = session.post(f"{url_prefix}/web/login/logout.do")
    return response.json()


def save_topology(url_prefix):
    response = session.post(
        f"{url_prefix}/cvpservice/provisioning/v2/saveTopology.do", data=json.dumps([])
    )
    return response.json()


def add_configlet(url_prefix, configlet_name, configlet_body):
    temp_data = json.dumps({"config": configlet_body, "name": configlet_name})
    response = session.post(
        f"{url_prefix}/cvpservice/configlet/addConfiglet.do", data=temp_data
    )
    # return temp_data
    return response.json()


def upload_image(url_prefix, image_name):
    with open(image_name, "rb") as image_binary:
        image_dict = {"file": image_binary}
        response = session.post(
            f"{url_prefix}/cvpservice/image/addImage.do", files=image_dict
        )
    return response.json()


def add_bundle(url_prefix, image_bundle_name):
    data = {
        "images": [bundle_info, terminattr_info],
        "isCertifiedImage": "true",
        "name": "DefaultBundle",
    }
    response = session.post(
        f"{url_prefix}/cvpservice/image/saveImageBundle.do", data=json.dumps(data)
    )
    return response.json()


def add_container(url_prefix, container_name):
    data = {
        "data": [
            {
                "info": f"adding Container {container_name}",
                "infoPreview": container_name,
                "action": "add",
                "nodeType": "container",
                "nodeId": container_name,
                "toId": "root",
                "fromId": "",
                "nodeName": container_name,
                "fromName": "",
                "toName": "Tenant",
                "toIdType": "container",
            }
        ]
    }
    response = session.post(
        f"{url_prefix}/cvpservice/ztp/addTempAction.do?format=topology&queryParam=&nodeId=root",
        data=json.dumps(data),
    )
    print(json.dumps(data))
    return response.json()


def add_configlet(url_prefix, configlet_name, configlet_body):
    temp_data = json.dumps({"config": configlet_body, "name": configlet_name})
    response = session.post(
        f"{url_prefix}/cvpservice/configlet/addConfiglet.do", data=temp_data
    )
    # return temp_data
    return response.json()


def add_configlet_builder(url_prefix, builder_name, builder_body):
    temp_data = json.dumps(
        {"name": builder_name, "data": {"main_script": {"data": builder_body}}}
    )
    response = session.post(
        f"{url_prefix}/cvpservice/configlet/addConfigletBuilder.do?isDraft=false",
        data=temp_data,
    )
    return response.json()


# Login
print("###### Logging into Server 1")
login(server1, username, password)
# Upload Image Bundle SWI File
print("###### Uploading Image Bundle")
try:
    bundle_info = upload_image(server1, image_name)
except Exception as e:
    print("Failure to upload file. Does it exist already? Is it in the working dir?")
bundle_info.pop("result", None)
# Upload Image Bundle TerminAttr SWIX
try:
    terminattr_info = upload_image(server1, terminattr)
except Exception as e:
    print("Failure to upload file. Does it exist already? Is it in the working dir?")
bundle_info.pop("result", None)
terminattr_info.pop("result", None)
# Create Image Bundle with both SWI and SWIX
try:
    add_bundle(server1, json.dumps(bundle_info, terminattr_info))
except Exception as e:
    print("Add bundle failed for some reason...")
# Create Container Structure
for container in containers_to_build:
    try:
        add_container(server1, container)
    except Exception as e:
        pass
# Upload Configlets / Builders
configlets = os.listdir("./Configlets")
for configlet in configlets:
    if configlet.endswith(".py"):
        with open(f"./Configlets/{configlet}", "r") as f:
            output = add_configlet_builder(server1, configlet, f.read())
            print(output)
    else:
        with open(f"./Configlets/{configlet}", "r") as f:
            output = add_configlet(server1, configlet, f.read())
            print(output)
