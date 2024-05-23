import logging
import os
import boto3

from random import random
import json
import urllib.request

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)


class XpressLicenseManager:

    LICENSES = "/nrel/engage/xpress/licenses"
    LICENSE_PATH = '/usr/local/xpressmp/bin/xpauth.xpr'
    MAC_PATH = '/usr/local/xpressmp/bin/xpauth.mac'

    def __init__(self):
        self.ssm = boto3.client("ssm", "us-west-2")

    def get_license(self):
        metadata = self._fetch_container_metadata()
        task_definition = metadata["Family"].lower()

        item = task_definition.split("-")[-1]
        if not item.startswith("mx"):
            with open(self.MAC_PATH, "w") as fm:
                fm.write("98:F2:B3:9F:5D:00")  # A fake mac address for software dummy run
                fm.close()
            return None

        # ECS Deployment: engage-{env}
        if item in ["test", "dev", "prod"]:
            deploy_env = item
            licenses = self._fetch_licenses_mapping()[deploy_env]
            seed = int(random()*1000000)
            index = seed % len(licenses)
            license = licenses[index]
            logger.info("Get license for ECS task deployment: %s", json.dumps(license))

        # Batch job definition pattern: engage-cpux-memx-{env}-{licenseId}
        else:
            license_id = item
            license = {
                "mac_address": license_id,
                "parameter_name": f"/nrel/engage/batch/license-{license_id}"
            }
            logger.info("Get license for Batch task deployment: %s", json.dumps(license))

        return license

    def _fetch_container_metadata(self):
        url = "%s/task" % os.environ["ECS_CONTAINER_METADATA_URI"]
        json_data = urllib.request.urlopen(url).read().decode("utf-8")
        return json.loads(json_data)

    def _fetch_licenses_mapping(self):
        response = self.ssm.get_parameter(
            Name=self.LICENSES,
            WithDecryption=True
        )
        licenses = json.loads(response["Parameter"]["Value"])
        return licenses

    def install_license(self, license):
        response = self.ssm.get_parameter(
            Name=license["parameter_name"],
            WithDecryption=True
        )

        # xpauth.xpr
        body = response["Parameter"]["Value"]
        with open(self.LICENSE_PATH, "w") as fx:
            fx.write(body)
            fx.close()

        # xpauth.mac
        hostid = license["mac_address"][2:]
        mac_address = ':'.join(hostid[i:i + 2] for i in range(0, 12, 2)).upper()
        logger.info("export XPRESS_MAC=%s", mac_address)
        with open(self.MAC_PATH, "w") as fm:
            fm.write(mac_address)
            fm.close()


if __name__ == "__main__":
    manager = XpressLicenseManager()
    license = manager.get_license()
    if license:
        manager.install_license(license)
