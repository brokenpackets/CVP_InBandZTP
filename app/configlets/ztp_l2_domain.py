from cvplibrary import CVPGlobalVariables, GlobalVariableNames, Device

VLAN_ID = 1

# Check if device is in ZTP mode
if CVPGlobalVariables.getValue(GlobalVariableNames.ZTP_STATE) == "true":
    device_ip = CVPGlobalVariables.getValue(GlobalVariableNames.CVP_IP)
    device_user = CVPGlobalVariables.getValue(GlobalVariableNames.ZTP_USERNAME)
    device_pass = CVPGlobalVariables.getValue(GlobalVariableNames.ZTP_PASSWORD)
    device = Device(device_ip, device_user, device_pass)
    SVIConfig = device.runCmds(
        ["enable", "interface vlan " + str(VLAN_ID), "ip address dhcp"]
    )[1]["response"]
    iflist = device.runCmds(["enable", "show interfaces status"])[1]["response"]
    for item in iflist["interfaceStatuses"].keys():
        if item.startswith("Ethernet"):
            device.runCmds(
                [
                    "enable",
                    "configure",
                    "interface " + item,
                    "switchport",
                    "switchport mode access",
                    "switchport access vlan " + str(VLAN_ID),
                ]
            )
