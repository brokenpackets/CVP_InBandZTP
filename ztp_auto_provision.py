#!/usr/bin/env python

import logging
from typing import Any

from ruamel.yaml import YAML

from cloudvision import ConvCloudVision, CvpWarning


logging.basicConfig(level="DEBUG")


def load_yaml(data) -> Any:
    return YAML(typ="safe").load(data)


def main():
    server = "cvp-green.lab.tedor.org"
    username = "cvpadmin"
    password = "Arista123"

    with ConvCloudVision(server, username, password, verify=False) as cvp:
        seed_raw = cvp.get_configlet_by_name("ztp_seed_data.yaml")
        seed_data = load_yaml(seed_raw.get("config"))

        ztp_devices = [
            device
            for device in cvp.get_inventory_devices()
            if device["parentContainerKey"] == "undefined_container"
        ]
        for device in ztp_devices:
            data = next(
                (d for d in seed_data if d["serial"] == device["serialNumber"]), None,
            )
            if data is None:
                continue

            container_name = data.get("container")
            device_id = device.get("systemMacAddress")
            device_name = device.get("fqdn")
            device_new_name = data.get("name")
            try:
                cvp.move_device_to_container(container_name, device_name)
            except CvpWarning:
                pass

            proposed_configlets = cvp.get_temp_configs_by_net_element_id(device_id).get(
                "proposedConfiglets"
            )
            ds_configlets = cvp.search_configlets(f"ds_{device_new_name}_").get("data")
            cvp.associate_configlets(
                configlets=proposed_configlets + ds_configlets,
                device_name=device_name,
                save=True,
            )


if __name__ == "__main__":
    main()
