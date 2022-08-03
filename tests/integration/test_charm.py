#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.


import logging
import pathlib

import pytest
import requests
import tenacity
import yaml
from pytest_operator import plugin as pytest_plugin

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(pathlib.Path("./metadata.yaml").read_text())
APP_NAME = METADATA["name"]
POSTGRESQL_CHARM = "postgresql-k8s"
NGINX_INGRESS_CHARM = "nginx-ingress-integrator"


# When the Waltz container starts, it is running Liquibase before starting the service itself.
# We should retry a few times, to give it time to start the Waltz service.
# Similarly, when the Ingress Route is being established, it takes a few seconds to take effect.
@tenacity.retry(
    retry=tenacity.retry_if_result(lambda x: x is False),
    stop=tenacity.stop_after_attempt(5),
    wait=tenacity.wait_exponential(multiplier=1, min=5, max=30),
)
def check_waltz_connection(url, headers=None):
    """Tests the connection to the given URL.

    Returns True if the response status code is 200, False in any other case.
    """
    logger.info("Trying to access Waltz...")
    try:
        response = requests.get(url, headers=headers)
        return response.status_code == 200
    except Exception as ex:
        logger.info(ex)

    return False


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: pytest_plugin.OpsTest):
    """Build the charm-under-test and deploy it together with related charms.

    Assert on the unit status before any relations/configurations take place.
    """
    # build and deploy charm from local source folder
    charm = await ops_test.build_charm(".")
    resources = {"waltz-image": METADATA["resources"]["waltz-image"]["upstream-source"]}
    await ops_test.model.deploy(charm, resources=resources, application_name=APP_NAME)

    # Deploy the needed postgresql-k8s charm and relate it to the waltz charm.
    await ops_test.model.deploy(POSTGRESQL_CHARM)

    # issuing dummy update_status just to trigger an event
    await ops_test.model.set_config({"update-status-hook-interval": "10s"})

    # Wait for it to become active.
    await ops_test.model.wait_for_idle(apps=[POSTGRESQL_CHARM], status="active", timeout=2000)

    # Relate the 2 charms together.
    await ops_test.model.add_relation("%s:db" % APP_NAME, "%s:db" % POSTGRESQL_CHARM)

    # Wait for the Waltz charm to become active.
    await ops_test.model.wait_for_idle(apps=[APP_NAME], status="active", timeout=2000)

    assert ops_test.model.applications[APP_NAME].units[0].workload_status == "active"

    # effectively disable the update status from firing
    await ops_test.model.set_config({"update-status-hook-interval": "60m"})


@pytest.mark.abort_on_fail
async def test_application_is_up(ops_test: pytest_plugin.OpsTest):
    status = await ops_test.model.get_status()
    unit_name = "%s/0" % APP_NAME
    address = status["applications"][APP_NAME]["units"][unit_name]["address"]

    url = "http://%s:8080" % address
    can_connect = check_waltz_connection(url)

    assert can_connect, "Could not reach Waltz through its IP."

    logger.info("Successfully reached Waltz through its IP.")


@pytest.mark.abort_on_fail
async def test_nginx_ingress_integration(ops_test: pytest_plugin.OpsTest):
    # Deploy the optional nginx-ingress-integrator charm and relate it to the waltz charm.
    await ops_test.model.deploy(NGINX_INGRESS_CHARM, trust=True)
    await ops_test.model.add_relation(APP_NAME, NGINX_INGRESS_CHARM)

    # Wait for it to become Active.
    await ops_test.model.wait_for_idle(apps=[NGINX_INGRESS_CHARM], status="active", timeout=1000)
    assert ops_test.model.applications[NGINX_INGRESS_CHARM].units[0].workload_status == "active"

    # We should now be able to connect to Waltz through it's service-hostname (by default, its
    # application name). In this test scenario, we don't have a resolver for it. One could
    # configure the /etc/hosts file to have the line:
    # 127.0.0.1 finos-waltz-k8s
    # Having the line above would resolve the hostname. For the current testing purposes, we
    # can simply connect to 127.0.0.1 and having the hostname as a header. This is the
    # equivalent of:
    # curl --header 'Host: finos-waltz-k8s' http://127.0.0.1

    url = "http://127.0.0.1"
    headers = {"Host": APP_NAME}
    can_connect = check_waltz_connection(url, headers)

    assert can_connect, "Could not reach Waltz through its service-hostname."

    logger.info("Successfully reached Waltz through its service-hostname.")
