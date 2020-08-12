#!/usr/bin/env python
import requests
import json
import yaml

###### User Variables

username = "admin"
password = "Arista123"
server1 = "https://192.168.255.50"
container_name = "Tenant"
yaml_name = "ztp_SeedData.yaml"

###### Do not modify anything below this line. Or do, I'm not a cop.
connect_timeout = 10
headers = {"Accept": "application/json", "Content-Type": "application/json"}
requests.packages.urllib3.disable_warnings()
session = requests.Session()


def login(url_prefix, username, password):
    authdata = {"userId": username, "password": password}
    headers.pop("APP_SESSION_ID", None)
    response = session.post(
        url_prefix + "/web/login/authenticate.do",
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
    response = session.post(url_prefix + "/web/login/logout.do")
    return response.json()


def get_inventory(url_prefix):
    response = session.get(url_prefix + "/cvpservice/inventory/devices")
    if response.json():
        return response.json()


def get_builder(url_prefix, builder_name):
    response = session.get(
        url_prefix + "/cvpservice/configlet/getConfigletByName.do?name=" + builder_name
    )
    if response.json()["key"]:
        return response.json()["key"]


def get_container_configlets(url_prefix, container_key):
    response = session.get(
        url_prefix
        + "/cvpservice/ztp/getTempConfigsByContainerId.do?containerId="
        + container_key
    )
    return response.json()


def get_configlets_by_device(url_prefix, deviceMac):
    response = session.get(
        url_prefix
        + "/cvpservice/provisioning/getConfigletsByNetElementId.do?netElementId="
        + deviceMac
        + "&startIndex=0&endIndex=0"
    )
    return response.json()


def get_configlet_by_name(url_prefix, configletname):
    response = session.get(
        url_prefix + "/cvpservice/configlet/getConfigletByName.do?name=" + configletname
    )
    return response.json()


def search_configlets(url_prefix, configletname):
    response = session.get(
        url_prefix
        + "/cvpservice/configlet/searchConfiglets.do?type=static&queryparam="
        + configletname
        + "&startIndex=0&endIndex=0"
    )
    return response.json()


def get_container(url_prefix, container_name):
    response = session.get(
        url_prefix
        + "/cvpservice/provisioning/searchTopology.do?queryParam="
        + container_name
        + "&startIndex=0&endIndex=0"
    )
    if response.json()["containerList"][0]["key"]:
        return response.json()["containerList"][0]["key"]


def get_temp_configs(url_prefix, nodeId):
    response = session.get(
        url_prefix + "/cvpservice/provisioning/getTempConfigsByNetElementId."
        "do?netElementId=" + nodeId
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
        url_prefix + "/cvpservice/configlet/autoConfigletGenerator.do", data=data
    )
    return response.json()


def save_topology(url_prefix):
    response = session.post(
        url_prefix + "/cvpservice/provisioning/v2/saveTopology.do", data=json.dumps([])
    )
    return response.json()


def apply_configlets(url_prefix, nodeName, nodeIp, deviceMac, newConfiglets):
    configlets = get_configlets_by_device(url_prefix, deviceMac)
    cnames = []
    ckeys = []

    # Add the new configlets to the end of the arrays
    for entry in newConfiglets:
        cnames.append(entry["name"])
        ckeys.append(entry["key"])

    info = "ZTPBuilder: Configlet Assign: to Device " + nodeName
    info_preview = "<b>Configlet Assign:</b> to Device " + nodeName
    tempData = json.dumps(
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
                    "toId": deviceMac,
                    "toIdType": "netelement",
                    "fromId": "",
                    "nodeName": "",
                    "fromName": "",
                    "toName": nodeName,
                    "nodeIpAddress": nodeIp,
                    "nodeTargetIpAddress": nodeIp,
                    "childTasks": [],
                    "parentTask": "",
                }
            ]
        }
    )

    response = session.post(
        url_prefix
        + "/cvpservice/ztp/addTempAction.do?format=topology&queryParam=&nodeId=root",
        data=tempData,
    )
    # return tempData
    return response.json()


def move_device(url_prefix, nodeName, nodeId, toId, toName):
    tempData = json.dumps(
        {
            "data": [
                {
                    "info": "Device "
                    + toName
                    + "move from undefined to Container "
                    + toId,
                    "infoPreview": "<b>Device ZTP Add:</b> " + toName,
                    "action": "update",
                    "nodeType": "netelement",
                    "nodeId": nodeId,
                    "toId": toId,
                    "fromId": "undefined_container",
                    "nodeName": nodeName,
                    "toName": toName,
                    "toIdType": "container",
                }
            ]
        }
    )
    response = session.post(
        url_prefix
        + "/cvpservice/ztp/addTempAction.do?format=topology&queryParam=&nodeId=root",
        data=tempData,
    )
    # return tempData
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
    tempData = json.dumps(
        {
            "data": [
                {
                    "info": "Configlet Assign: to container " + container_name,
                    "infoPreview": "<b>Configlet Assign:</b> to container "
                    + container_name,
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
        url_prefix
        + "/cvpservice/ztp/addTempAction.do?format=topology&queryParam=&nodeId=root",
        data=tempData,
    )
    # return tempData
    return response.json()


print("###### Logging into Server 1")
login(server1, username, password)
print("###### Pulling down YAML File")
yamlfile = get_configlet_by_name(server1, yaml_name)["config"]
yamlbody = yaml.load(yamlfile)
print("###### Getting list of devices in Undefined Container")
ztpdevices = get_inventory(server1)
for device in ztpdevices:
    if device["parentContainerKey"] == "undefined_container":
        for template in yamlbody:
            if yamlbody[template]["Serial"] == device["serialNumber"]:
                nodeName = device["fqdn"]
                nodeId = device["systemMacAddress"]
                toId = get_container(server1, yamlbody[template]["container"])
                toName = template
                nodeIp = device["ipAddress"]
                move = move_device(server1, nodeName, nodeId, toId, toName)
                ds_configlets = search_configlets(server1, "DS_" + template + "_")
                print(ds_configlets)
                # configletList = get_configlets_by_device(server1,nodeId)
                tempConfiglets = get_temp_configs(server1, nodeId)
                newConfiglets = tempConfiglets["proposedConfiglets"]
                dsList = []
                if int(ds_configlets["total"]) > 0:
                    for config in ds_configlets["data"]:
                        output = get_configlet_by_name(server1, config["name"])
                        dsList.extend([output])
                    newConfiglets.extend(dsList)
                    print("Assigning DS Configlets to " + nodeName)
                    assign = apply_configlets(
                        server1, nodeName, nodeIp, nodeId, newConfiglets
                    )
# Once temp action created, save will cause it to be committed, and generate
# the tasks to run against devices. Can automate running them if needed, but
# I generally prefer manual runs to validate it did what I expected.
print("##### Saving Topology")
# save = save_topology(server1)
# logout(server1)
print("##### Complete")

