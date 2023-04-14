# FINOS Waltz Charmed Operator developer's guide

## Prerequisites

In order to start developing and contributing to the FINOS Waltz Charmed Operator, make sure you have an environment in which you can deploy it. If you do not have one, you can create a Microk8s environment.

Here is a [Local Deployment](https://github.com/finos/waltz-juju-bundle/blob/main/docs/guides/LocalDeployment.md) guide that will get you set up with a proper environment in which you can develop and deploy charms in. The guide also contains information on how to install Juju, bootstrap a Controller, create a Juju model, and deploy the `postgresql-k8s` charm and relate it to the Waltz charm.

In addition to that, you will need to install Charmcraft, which we'll use to build the Charm. For more information on how to install Charmcraft, check the Charmcraft section of the [dev-setup](https://juju.is/docs/sdk/dev-setup)

## Developing

After you've created the necessary changes and making sure that the [unit tests](#Testing) pass, run the following command to build the charm:

```bash
charmcraft pack
```

When building the Charm for the first time, it will take a bit longer, but subsequent builds will be significantly faster.

If there are any errors during building check the log file mentioned by Charmcraft. If you have added a new dependency in ``requirements.txt`` that is dependent on another package being installed, add that dependency in ``charmcraft.yaml`` in the ``build-packages`` section. For example, some python packages might require ``python3-dev`` to be installed. In that case, we add the following in ``charmcraft.yaml``:

```
parts:
  charm:
    build-packages:
      - python3-dev
```

If there are any other issues, ``charmcraft clean`` might help.

After the charm has been built, you will be able to find it in the local folder. You can then deploy it with the command:

```bash
juju deploy ./finos-waltz-k8s_ubuntu-20.04-amd64.charm --resource waltz-image=ghcr.io/finos/waltz
```

If it was already deployed, you can simply refresh it:

```bash
juju refresh --path=./finos-waltz-k8s_ubuntu-20.04-amd64.charm
```

Doing a ``juju refresh`` / ``juju upgrade-charm`` has the benefit of keeping any configurations or relations added previously. Keep in mind that if you want want to use a different Container Image than the charm has been deployed with, you will have to remove the application first, and add it manually, and then add the necessary configurations:

```bash
juju remove-application finos-waltz-k8s
juju deploy ./finos-waltz-k8s_ubuntu-20.04-amd64.charm --resource waltz-image=<another-image>
```

## Testing

Any new functionality added will have to be covered through unit tests. After writing the necessary unit tests, you can run them with:

```bash
tox -e unit
```

Additionally, make sure that the integration tests are working properly with your changes. Running the integration tests will require you to have a bootstrapped controller. You can run the integration tests with the following command:

```bash
tox -e integration
```

Before pushing the local changes and submitting a Pull Request, make sure that your code is properly formatted and that there are no linting errors:

```bash
tox -e fmt
tox -e lint
```

After the Pull Request was created and merged, the ``Publish Charm`` [Github action](../.github/workflows/publish.yaml) will run, which will build the charm and publish it to Charmhub on the edge channel. You can read [here](CharmPublishing.md) for more information about it.

## Known issues

```
err: ERROR starting proxy for api connection: connecting k8s proxy: Get "https://127.0.0.1:16443/api/v1/namespaces/controller-waltz-public-v3/services/controller-service": x509: certificate has expired or is not yet valid: current time 2023-04-09T00:00:52Z is after 2023-04-08T14:34:12Z
```
See example on https://github.com/finos/waltz-integration-juju/actions/runs/4647710763/jobs/8224851693#step:3:51 .

This normally means that Kubernetes' credentials (which is a certificate) have expired. These credentials have 1 year TTL by default and can be easily renewed by running the following commands on the Waltz demo box:

```
# need to be root for this.
sudo su

# check the certificates and their TTL.
microk8s refresh-certs -c

# refresh them.
microk8s refresh-certs -e server.crt
microk8s refresh-certs -e front-proxy-client.crt
```
