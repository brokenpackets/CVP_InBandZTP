import logging
from typing import Any, List, Optional, Set, Union

import requests

log = logging.getLogger("cvpy")


class CvpError(RuntimeError):
    pass


class CvpWarning(RuntimeWarning):
    pass


class CloudVision:
    def __init__(
        self,
        server: str,
        username: str,
        password: str,
        timeout: Optional[int] = None,
        verify: Optional[bool] = True,
    ) -> None:
        self.server = server
        self.username = username
        self.password = password

        self.timeout = timeout
        self.verify = verify
        if not self.verify:
            import urllib3

            urllib3.disable_warnings()

        self.session = requests.Session()

    def __delete__(self):
        self._logout()

    def __enter__(self):
        self._login()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._logout()

    def _add_temp_action(self, payload: Any, warnings: Optional[Set[int]] = {}) -> Any:
        endpoint = "cvpservice/ztp/addTempAction.do"
        params = ["format=topology", "queryParam", "nodeId=root"]
        return self._post(
            endpoint, params=params, payload={"data": [payload]}, warnings=warnings
        )

    def _get(
        self,
        endpoint: str,
        params: Optional[Union[List[str], str]] = [],
        warnings: Optional[Set[int]] = [],
    ) -> Any:
        if params:
            if isinstance(params, list):
                params = "&".join(param for param in params if param)
            endpoint = "?".join([endpoint, params])
        response = self.session.get(f"https://{self.server}/{endpoint}")
        response.raise_for_status()
        json = response.json()
        try:
            if error_code := json.get("errorCode"):
                if int(error_code) not in warnings:
                    raise CvpError(json)
                else:
                    log.warning(json)
                    raise CvpWarning(json)
        except AttributeError:
            return json
        return json

    def _login(self) -> str:
        endpoint = "web/login/authenticate.do"
        payload = {"userId": self.username, "password": self.password}
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        response = self._post(endpoint, payload=payload, headers=headers)
        session_id = response.get("sessionId")
        if not session_id:
            log.error(response)
            raise CvpError(response)

    def _logout(self):
        endpoint = "web/login/logout.do"
        self._post(endpoint)

    def _post(
        self,
        endpoint: str,
        params: Optional[Union[List[str], str]] = "",
        payload: Optional[Any] = None,
        warnings: Optional[Set[int]] = {},
        **kwargs,
    ) -> Any:
        if params:
            if isinstance(params, list):
                params = "&".join(param for param in params if param)
            endpoint = "?".join([endpoint, params])
        response = self.session.post(
            f"https://{self.server}/{endpoint}",
            json=payload,
            timeout=self.timeout,
            verify=self.verify,
            **kwargs,
        )
        response.raise_for_status()
        json = response.json()
        if error_code := json.get("errorCode"):
            if int(error_code) in warnings:
                log.warning(json)
                raise CvpWarning(json)
            else:
                log.error(json)
                raise CvpError(json)
        return json

    def _save_topology(self, payload: Optional[Any] = []):
        endpoint = "cvpservice/provisioning/v2/saveTopology.do"
        return self._post(endpoint, payload=payload)

    def add_configlet(self, data: str, name: str):
        endpoint = "cvpservice/configlet/addConfiglet.do"
        payload = {"config": data, "name": name}
        warnings = {
            132518,  # Data already exists in Database
        }
        return self._post(f"{endpoint}", payload=payload, warnings=warnings)

    def add_configlet_builder(self, data: str, name: str):
        endpoint = "cvpservice/configlet/addConfigletBuilder.do"
        params = "isDraft=false"
        payload = {"name": name, "data": {"main_script": {"data": data}}}
        warnings = {
            132823,  # Configlet builder name already exist
        }
        return self._post(endpoint, params=params, payload=payload, warnings=warnings)

    def add_container(
        self,
        container_name: str,
        to_id: str,
        to_name: str,
        info: Optional[str] = None,
        save: Optional[bool] = False,
    ):
        payload = {
            "info": info,
            "infoPreview": info,
            "note": "",
            "action": "add",
            "nodeType": "container",
            "nodeId": container_name,
            "toId": to_id,
            "toIdType": "container",
            "fromId": "",
            "nodeName": container_name,
            "fromName": "",
            "toName": to_name,
            "childTasks": [],
            "parentTask": "",
        }
        warnings = {
            122518,  # Data already exists in Database
        }
        response = self._add_temp_action(payload, warnings=warnings)
        if save:
            self._save_topology()
        return response

    def add_image(self, image: str) -> Any:
        with open(image, "rb") as io:
            endpoint = "cvpservice/image/addImage.do"
            warnings = {
                162876,  # Upload failed: Image with the same name already exists
            }
            files = {"file": io}
            return self._post(endpoint, warnings=warnings, files=files)

    def associate_image_bundle(
        self,
        bundle_id: str,
        bundle_name: str,
        to_id_type: str,
        to_id: str,
        to_name: str,
        info: Optional[str] = None,
        save: Optional[bool] = False,
    ):
        payload = {
            "info": info,
            "infoPreview": info,
            "note": "",
            "action": "associate",
            "nodeType": "imagebundle",
            "nodeId": bundle_id,
            "toId": to_id,
            "toIdType": to_id_type,
            "fromId": "",
            "nodeName": bundle_name,
            "fromName": "",
            "toName": to_name,
            "childTasks": [],
            "parentTask": "",
        }
        response = self._add_temp_action(payload)
        if save:
            self._save_topology()
        return response

    def get_configlet_by_name(self, name: str) -> Any:
        endpoint = "cvpservice/configlet/getConfigletByName.do"
        params = f"name={name or ''}"
        return self._get(endpoint, params=params)

    def get_configlets_by_device(
        self, net_element_id: str, start: Optional[int] = 0, end: Optional[int] = 0,
    ) -> Any:
        endpoint = "cvpservice/provisioning/getConfigletsByNetElementId.do"
        params = [
            f"netElementId={net_element_id or ''}",
            f"startIndex={start}",
            f"endIndex={end}",
        ]
        return self._get(endpoint, params=params)

    def get_image_bundle_by_name(self, name: str) -> Any:
        endpoint = "cvpservice/image/getImageBundleByName.do"
        params = f"name={name}"
        warnings = {
            162801,  # Entity does not exist
        }
        return self._get(endpoint, params=params, warnings=warnings)

    def get_image_bundles(
        self,
        query: Optional[str] = None,
        start: Optional[int] = 0,
        end: Optional[int] = 0,
    ) -> Any:
        endpoint = "cvpservice/image/getImageBundles.do"
        params = [
            f"queryparam={query or ''}",
            f"startIndex={start}",
            f"endIndex={end}",
        ]
        return self._get(endpoint, params=params)

    def get_images(
        self,
        query: Optional[str] = None,
        start: Optional[int] = 0,
        end: Optional[int] = 0,
    ) -> Any:
        endpoint = "cvpservice/image/getImages.do"
        params = [
            f"queryparam={query or ''}",
            f"startIndex={start}",
            f"endIndex={end}",
        ]
        return self._get(endpoint, params=params)

    def get_inventory_devices(self):
        endpoint = "cvpservice/inventory/devices"
        return self._get(endpoint)

    def get_temp_configs_by_net_element_id(self, net_element_id: str) -> Any:
        endpoint = "cvpservice/provisioning/getTempConfigsByNetElementId.do"
        params = f"netElementId={net_element_id or ''}"
        return self._get(endpoint, params=params)

    def save_image_bundle(
        self, name: str, *images: str, certified: Optional[bool] = True,
    ) -> Any:
        # warnings = {
        #     162518,  # Failure - Data already exists in Database
        # }
        endpoint = "cvpservice/image/saveImageBundle.do"
        payload = {
            "images": images,
            "isCertifiedImage": "true" if certified else "false",
            "name": name,
        }
        return self._post(endpoint, payload=payload)

    def search_configlets(
        self, query: str, start: Optional[int] = 0, end: Optional[int] = 0
    ) -> Any:
        endpoint = "cvpservice/configlet/searchConfiglets.do"
        params = [
            "type=static",
            f"queryparam={query or ''}",
            f"startIndex={start}",
            f"endIndex={end}",
        ]
        return self._get(endpoint, params=params)

    def search_topology(
        self,
        query: Optional[str] = None,
        start: Optional[int] = 0,
        end: Optional[int] = 0,
    ) -> Any:
        endpoint = "cvpservice/provisioning/searchTopology.do"
        params = [
            f"queryParam={query or ''}",
            f"startIndex={start}",
            f"endIndex={end}",
        ]
        return self._get(endpoint, params=params)

    # def update_netelement(
    #     self,
    #     from_id: str,
    #     node_id: str,
    #     node_name: str,
    #     to_id_type: str,
    #     to_id: str,
    #     to_name: str,
    #     info: Optional[str] = None,
    #     save: Optional[bool] = False,
    # ):
    #     payload = {
    #         "info": info,
    #         "infoPreview": info,
    #         "action": "update",
    #         "nodeType": "netelement",
    #         "nodeId": node_id,
    #         "toId": to_id,
    #         "fromId": from_id,
    #         "nodeName": node_name,
    #         "toName": to_name,
    #         "toIdType": to_id_type,
    #     }
    #     response = self._add_temp_action(payload)
    #     if save:
    #         self._save_topology()
    #     return response


class ConvCloudVision(CloudVision):
    def _get_or_add_image(self, image_name: str) -> Any:
        response = self.get_images(query=image_name)
        if response.get("total", 0) > 0:
            image_data = next(
                (
                    image
                    for image in response.get("data", [])
                    if image.get("name") == image_name
                ),
                None,
            )
            if image_data:
                return image_data
        return self.add_image(image_name)

    def _get_or_save_image_bundle(self, bundle_name: str, *image_names: str) -> Any:
        try:
            return self.get_image_bundle_by_name(name=bundle_name)
        except CvpWarning:
            self.save_image_bundle(bundle_name, *image_names)
            return self.get_image_bundle_by_name(name=bundle_name)

    def associate_configlets(
        self, configlets: list, device_name: str, target_ip: Optional[str] = None, save: Optional[bool] = False
    ) -> Any:
        device = self.get_device_by_name(device_name)
        device_id = device.get("key")
        device_ip = device.get("ipAddress")

        configlet_names = []
        configlet_keys = []
        for configlet in configlets:
            configlet_names.append(configlet["name"])
            configlet_keys.append(configlet["key"])

        info = f"Assign configlets to {device_name}"
        payload = {
            "info": info,
            "infoPreview": info,
            "note": "",
            "action": "associate",
            "nodeType": "configlet",
            "nodeId": "",
            "configletList": configlet_keys,
            "configletNamesList": configlet_names,
            "ignoreConfigletNamesList": [],
            "ignoreConfigletList": [],
            "configletBuilderList": [],
            "configletBuilderNamesList": [],
            "ignoreConfigletBuilderList": [],
            "ignoreConfigletBuilderNamesList": [],
            "toId": device_id,
            "toIdType": "netelement",
            "fromId": "",
            "nodeName": "",
            "fromName": "",
            "toName": device_name,
            "nodeIpAddress": device_ip,
            "nodeTargetIpAddress": target_ip or device_ip,
            "childTasks": [],
            "parentTask": "",
        }
        response = self._add_temp_action(payload)
        if save:
            self._save_topology()
        return response

    def create_image_bundle(self, bundle_name: str, *image_names: str) -> Any:
        image_data = []
        for image_name in image_names:
            response = self._get_or_add_image(image_name)
            image_data.append(response)
        return self._get_or_save_image_bundle(bundle_name, *image_data)

    def get_container_by_name(self, container_name: str) -> str:
        response = self.search_topology(container_name)
        if containers := response.get("containerList"):
            return containers[0]

    def get_device_by_name(self, device_name: str) -> str:
        response = self.search_topology(device_name)
        if devices := response.get("netElementList"):
            return devices[0]

    def get_configlets_by_device_name(self, device_name: str) -> Any:
        if device := self.get_device_by_name(device_name):
            device_id = device.get("key")
            return self.get_configlets_by_device(net_element_id=device_id)

    def move_device_to_container(
        self, container_name: str, device_name: str, save: Optional[bool] = False
    ) -> Any:
        to_container_id = self.get_container_by_name(container_name).get("key")
        if device := self.get_device_by_name(device_name):
            device_id = device.get("key")
            from_container_id = device.get("parentContainerId")
        else:
            return

        info = f"Move {device_name} to {container_name}"
        payload = {
            "info": info,
            "infoPreview": info,
            "action": "update",
            "nodeType": "netelement",
            "nodeId": device_id,
            "toId": to_container_id,
            "fromId": from_container_id,
            "nodeName": device_name,
            "toName": container_name,
            "toIdType": "container",
        }
        warnings = {
            122518,  # Data already exists in Database
        }
        response = self._add_temp_action(payload, warnings=warnings)
        if save:
            self._save_topology()
        return response
