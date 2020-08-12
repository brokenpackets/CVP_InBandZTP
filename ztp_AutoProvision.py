#!/usr/bin/env python

import requests
import json
import yaml

# User Variables
username = "admin"
password = "Arista123"
server1 = "https://192.168.255.50"
container_name = "Tenant"
yaml_name = "ztp_SeedData.yaml"

# Do not modify anything below this line. Or do, I'm not a cop.
connect_timeout = 10
headers = {"Accept": "application/json", "Content-Type": "application/json"}
requests.packages.urllib3.disable_warnings()
session = requests.Session()


def login(url_prefix, username, password):
    authdata = {"userId": username, "password": password}
    headers.pop("APP_SESSION_ID", None)
    response = session.post(
        f"{url_prefix}/web/login/authenticate.do",
        data=json.dumps(authdata),
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


def get_inventory(url_prefix):
    response = session.get(f"{url_prefix}/cvpservice/inventory/devices")
    if response.json():
        return response.json()


def get_builder(url_prefix, builder_name):
    response = session.get(
        f"{url_prefix}/cvpservice/configlet/getConfigletByName.do?name={builder_name}"
    )
    if response.json()["key"]:
        return response.json()["key"]


def get_container_configlets(url_prefix, container_key):
    response = session.get(
        f"{url_prefix}/cvpservice/ztp/getTempConfigsByContainerId.do?containerId={container_key}"
    )
    return response.json()


def get_configlets_by_device(url_prefix, device_mac):
    response = session.get(
        f"{url_prefix}/cvpservice/provisioning/getConfigletsByNetElementId.do?netElementId={device_mac}&startIndex=0&endIndex=0"
    )
    return response.json()


def get_configlet_by_name(url_prefix, configlet_name):
    response = session.get(
        f"{url_prefix}/cvpservice/configlet/getConfigletByName.do?name={configlet_name}"
    )
    return response.json()


def search_configlets(url_prefix, configlet_name):
    response = session.get(
        f"{url_prefix}/cvpservice/configlet/searchConfiglets.do?type=static&queryparam={configlet_name}&startIndex=0&endIndex=0"
    )
    return response.json()


def get_container(url_prefix, container_name):
    response = session.get(
        f"{url_prefix}/cvpservice/provisioning/searchTopology.do?queryParam={container_name}&startIndex=0&endIndex=0"
    )
    if response.json()["containerList"][0]["key"]:
        return response.json()["containerList"][0]["key"]


def get_temp_configs(url_prefix, node_id):
    response = session.get(
        f"{url_prefix}/cvpservice/provisioning/getTempConfigsByNetElementId.do?netElementId={node_id}"
    )
    return response.json()


def run_builder(url_prefix, configlet_key, container_key):
    data = json.dumps(
        {
            "netElementIds": [],
            "configletBuilderId": configlet_key,
            "containerId": container_key,
            "pageType": "container",
        }
    )
    response = session.post(
        f"{url_prefix}/cvpservice/configlet/autoConfigletGenerator.do", data=data
    )
    return response.json()


def save_topology(url_prefix):
    response = session.post(
        f"{url_prefix}/cvpservice/provisioning/v2/saveTopology.do", data=json.dumps([])
    )
    return response.json()


def apply_configlets(url_prefix, node_name, node_ip, device_mac, new_configlets):
    configlets = get_configlets_by_device(url_prefix, device_mac)
    cnames = []
    ckeys = []

    # Add the new configlets to the end of the arrays
    for entry in new_configlets:
        cnames.append(entry["name"])
        ckeys.append(entry["key"])

    info = f"ZTPBuilder: Configlet Assign: to Device {node_name}"
    info_preview = f"<b>Configlet Assign:</b> to Device {node_name}"
    temp_data = json.dumps(
        {
            "data": [
                {
                    "info": info,
                    "infoPreview": info_preview,
                    "note": "",
                    "action": "associate",
                    "nodeType": "configlet",
                    "nodeId": "",
                    "configletList": ckeys,
                    "configletNamesList": cnames,
                    "ignoreConfigletNamesList": [],
                    "ignoreConfigletList": [],
                    "configletBuilderList": [],
                    "configletBuilderNamesList": [],
                    "ignoreConfigletBuilderList": [],
                    "ignoreConfigletBuilderNamesList": [],
                    "toId": device_mac,
                    "toIdType": "netelement",
                    "fromId": "",
                    "nodeName": "",
                    "fromName": "",
                    "toName": node_name,
                    "nodeIpAddress": node_ip,
                    "nodeTargetIpAddress": node_ip,
                    "childTasks": [],
                    "parentTask": "",
                }
            ]
        }
    )

    response = session.post(
        f"{url_prefix}/cvpservice/ztp/addTempAction.do?format=topology&queryParam=&nodeId=root",
        data=temp_data,
    )
    # return temp_data
    return response.json()


def move_device(url_prefix, node_name, node_id, to_id, to_name):
    temp_data = json.dumps(
        {
            "data": [
                {
                    "info": f"Device {to_name} move from undefined to Container {to_id}",
                    "infoPreview": f"<b>Device ZTP Add:</b> {to_name}",
                    "action": "update",
                    "nodeType": "netelement",
                    "nodeId": node_id,
                    "toId": to_id,
                    "fromId": "undefined_container",
                    "nodeName": node_name,
                    "toName": to_name,
                    "toIdType": "container",
                }
            ]
        }
    )
    response = session.post(
        f"{url_prefix}/cvpservice/ztp/addTempAction.do?format=topology&queryParam=&nodeId=root",
        data=temp_data,
    )
    # return temp_data
    return response.json()


def add_temp_action(
    url_prefix,
    container_name,
    container_key,
    current_static_key,
    current_static_name,
    current_builder_key,
    current_builder_name,
):
    temp_data = json.dumps(
        {
            "data": [
                {
                    "info": f"Configlet Assign: to container {container_name}",
                    "infoPreview": f"<b>Configlet Assign:</b> to container {container_name}",
                    "action": "associate",
                    "nodeType": "configlet",
                    "nodeId": "",
                    "toId": container_key,
                    "fromId": "",
                    "nodeName": "",
                    "fromName": "",
                    "toName": container_name,
                    "toIdType": "container",
                    "configletList": current_static_key,
                    "configletNamesList": current_static_name,
                    "ignoreConfigletList": [],
                    "ignoreConfigletNamesList": [],
                    "configletBuilderList": current_builder_key,
                    "configletBuilderNamesList": current_builder_name,
                    "ignoreConfigletBuilderList": [],
                    "ignoreConfigletBuilderNamesList": [],
                }
            ]
        }
    )

    response = session.post(
        f"{url_prefix}/cvpservice/ztp/addTempAction.do?format=topology&queryParam=&nodeId=root",
        data=temp_data,
    )
    # return temp_data
    return response.json()


print("###### Logging into Server 1")
login(server1, username, password)
print("###### Pulling down YAML File")
yaml_file = get_configlet_by_name(server1, yaml_name)["config"]
yaml_body = yaml.load(yaml_file)
print("###### Getting list of devices in Undefined Container")
ztp_devices = get_inventory(server1)
for device in ztp_devices:
    if device["parentContainerKey"] == "undefined_container":
        for template in yaml_body:
            if yaml_body[template]["Serial"] == device["serialNumber"]:
                node_name = device["fqdn"]
                node_id = device["systemMacAddress"]
                to_id = get_container(server1, yaml_body[template]["container"])
                to_name = template
                node_ip = device["ipAddress"]
                move = move_device(server1, node_name, node_id, to_id, to_name)
                ds_configlets = search_configlets(server1, f"DS_{template}_")
                print(ds_configlets)
                # configletList = get_configlets_by_device(server1,node_id)
                tempConfiglets = get_temp_configs(server1, node_id)
                new_configlets = tempConfiglets["proposedConfiglets"]
                ds_list = []
                if int(ds_configlets["total"]) > 0:
                    for config in ds_configlets["data"]:
                        output = get_configlet_by_name(server1, config["name"])
                        ds_list.extend([output])
                    new_configlets.extend(ds_list)
                    print(f"Assigning DS Configlets to {node_name}")
                    assign = apply_configlets(
                        server1, node_name, node_ip, node_id, new_configlets
                    )
# Once temp action created, save will cause it to be committed, and generate
# the tasks to run against devices. Can automate running them if needed, but
# I generally prefer manual runs to validate it did what I expected.
print("##### Saving Topology")
# save = save_topology(server1)
# logout(server1)
print("##### Complete")
