#!/usr/bin/env python

import logging

from ruamel.yaml import YAML

from cvpibztp.cloudvision import ConvCloudVision, CvpWarning
from cvpibztp.common import connection_details

logging.basicConfig(level="DEBUG")
log = logging.getLogger(__name__)


def load_yaml(data):
    return YAML(typ="safe").load(data)


def main():
    with ConvCloudVision(**connection_details()) as cvp:
        seed_raw = cvp.get_configlet_by_name("ztp_seed_data.yaml")
        seed_data = load_yaml(seed_raw.get("config"))

        ztp_devices = [
            device
            for device in cvp.get_inventory_devices()
            if device["parentContainerKey"] == "undefined_container"
        ]
        for device in ztp_devices:
            data = next(
                (d for d in seed_data if d["serial"] == device["serialNumber"]),
                None,
            )
            if data is None:
                continue

            container_name = data.get("container")
            device_id = device.get("systemMacAddress")
            device_raw_name = device.get("fqdn")
            device_new_name = data.get("name")
            device_proposed_ip = data.get("ip")
            try:
                cvp.move_device_to_container(container_name, device_raw_name)
            except CvpWarning:
                pass

            proposed_configlets = cvp.get_temp_configs_by_net_element_id(device_id).get(
                "proposedConfiglets"
            )
            ds_configlets = cvp.search_configlets(f"ds_{device_new_name}_").get("data")
            configlets = proposed_configlets + ds_configlets

            log.debug(configlets)
            if container_name in {"MGMT-ToR", "MGMT-Spine"}:
                configlet_builder_id = cvp.get_configlet_by_name(
                    "ztp_l2_domain.py"
                ).get("key")
                response = cvp.auto_configlet_generator(
                    configlet_builder_id, net_element_ids=[device_id]
                )
                builder = response["data"][0]["configlet"]
                configlets.append(builder)

            cvp.associate_configlets(
                configlets=configlets,
                device_name=device_raw_name,
                target_ip=device_proposed_ip,
                save=True,
            )


if __name__ == "__main__":
    main()
