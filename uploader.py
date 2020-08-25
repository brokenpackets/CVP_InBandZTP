#!/usr/bin/env python

import logging
from pathlib import Path

from cloudvision import ConvCloudVision, CvpWarning


logging.basicConfig(level="INFO")


def main():
    server = "cvp-green.lab.tedor.org"
    username = "cvpadmin"
    password = "Arista123"

    with ConvCloudVision(server, username, password, verify=False) as cvp:
        bundle_name = "DefaultBundle"
        image_names = {"EOS64-4.23.4.2M.swi", "TerminAttr-1.9.6-1.swix"}
        bundle_id = cvp.create_image_bundle(bundle_name, *image_names).get("id")
        _ = cvp.associate_image_bundle(
            bundle_id=bundle_id,
            bundle_name=bundle_name,
            to_id="root",
            to_id_type="container",
            to_name="Tenant",
            save=True,
        )

        changed = False
        containers = {"Leaf", "Spine", "MGMT-ToR", "MGMT-Spine"}
        for container in containers:
            try:
                _ = cvp.add_container(
                    container_name=container,
                    to_id="root",
                    to_name="Tenant",
                    save=False,
                )
                changed = True
            except CvpWarning:
                continue
        if changed:
            _ = cvp._save_topology()

        path = Path(__file__).parent / "configlets"
        configlets = path.iterdir()
        for configlet in configlets:
            if configlet.name.endswith(".py"):
                func = cvp.add_configlet_builder
            else:
                func = cvp.add_configlet
            try:
                func(data=configlet.read_text(), name=configlet.name)
            except CvpWarning:
                continue


if __name__ == "__main__":
    main()
