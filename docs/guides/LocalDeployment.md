# How to run Waltz locally using Charmed Operators

This tutorial will cover how to use Juju and Charmed Operators to deploy an instance of the [FINOS Waltz](https://waltz.finos.org/) charm on your local workstation, using [Microk8s](https://microk8s.io/). It can be used for evaluation and demonstration purposes, as well as development of new Waltz features.

These steps may be carried out on any Linux distribution that has a [Snap](https://snapcraft.io/) package manager installed. The steps in this tutorial have been tested on [Ubuntu 20.04](https://releases.ubuntu.com/focal/).

The deployment is composed by the following steps:

- [Install Microk8s](#Install-Microk8s)
- [Install Juju](#Install-Juju)
- [Bootstrap Juju](#Bootstrap-Juju)
- [Add the Juju Waltz Model](#Add-the-Juju-Waltz-Model)
- [Deploy the Waltz Bundle](#Deploy-the-Waltz-Bundle)
- [Use Waltz](#Use-Waltz)
- [Updating the Waltz Charm](#Updating-the-Waltz-charm) (optional)
- [Destroy setup](#Destroy-setup) (optional)

## Prerequisites

In order to deploy FINOS Waltz Charm, you will need to have Juju installed, and have a Kubernetes cluster to deploy it on. If you are missing them, follow the Juju and MicroK8s sections of the [dev-setup](https://juju.is/docs/sdk/dev-setup) guide.

In this guide, we'll be using ``waltz-controller`` as the name of the Juju controller. You are free to use any name other than `waltz-controller` but it must be consistent through the rest of this tutorial.

## Add the Juju Waltz Model

[Juju models](https://juju.is/docs/olm/models) are a logical grouping of applications and infrastructure that work together to deliver a service or product. In Kubernetes terms, models are effectively namespaces. Models are fundamental concepts in Juju and implement service isolation, access control, repeatability and boundaries.

You can add a new model with:

``` bash
juju add-model waltz-model
```

## Deploy the Waltz Bundle

When you deploy an charm with Juju, the installation code in the charmed operator will run and set up all the resources and environmental variables needed for the application to run properly. Deploying a bundle takes it a step further, it deploys a set of charms that can work together and relates them.

Deploy the finos-waltz-bundle in the finos-waltz model using the command line:

```bash
juju deploy --trust finos-waltz-bundle --channel=edge
```

The bundle contains the following charms: ``finos-waltz-k8s``, ``postgresql-k8s``, and ``nginx-ingress-integrator``. The bundle also creates creates relations between the ``finos-waltz-k8s`` charm and the ``postgresql-k8s`` and ``nginx-ingress-integrator`` charms.

In another terminal, you can check the deployment status and the integration code running using `watch --color juju status --color`. All the charms should become Active after a few minutes.

The FINOS Waltz charm will use the PostgreSQL database provisioned by the ``postgresql-k8s`` charm. Alternatively, you can configure it with an external PostgreSQL connection details:

```bash
juju config finos-waltz-k8s db-host="<db-host>" db-port="<db-port>" db-name="<db-name>" db-username="<db-username>" db-password="<db-password>"
```

Note that the relation with the `postgresql-k8s` charm takes precedence over the configuration options.

## Use Waltz

After the Charm became active, you can connect now connect to Waltz. Running ``juju status`` will reveal its IP:

```
Model  Controller        Cloud/Region        Version  SLA          Timestamp
waltz  finos-controller  microk8s/localhost  2.9.22   unsupported  09:06:52Z

App             Version                 Status  Scale  Charm            Store     Channel  Rev  OS          Address         Message
finos-waltz-k8s                         active      1  finos-waltz-k8s  charmhub  stable     2  kubernetes  10.152.183.143
postgresql-k8s  .../postgresql@ed0e37f  active      1  postgresql-k8s   charmhub  stable     3  kubernetes

Unit               Workload  Agent  Address       Ports     Message
finos-waltz/0*     active    idle   10.1.243.230
postgresql-k8s/0*  active    idle   10.1.243.196  5432/TCP  Pod configured
```

Simply connect to ``http://<WALTZ_IP>:8080``.

Alternatively, you can connect to the Waltz application through its ``finos-waltz`` name thanks to the ``nginx-ingress-integrator`` charm. For this, you will need add the following line in your `/etc/hosts` file:

```
127.0.1.1 finos-waltz
```

**Note:** If the Waltz deployment was done remotely on another machine, then instead of the IP above you should use the IP of that remote machine. This also applies for microk8s deployments on MacOS, in which case you can get the IP of the Multipass VM microk8s is deploy in with the command:

```bash
multipass list
```

The ``nginx-ingress-integrator`` charm has a few different configuration options that may be useful, including ``service-hostname`` option, which can be set to your publicly available DNS hostname.

## Updating the Waltz charm

If needed, you can rebuild the charm with ``charmcraft pack``, and update the charm directly:

```bash
juju upgrade-charm finos-waltz-k8s --path=./finos-waltz-k8s_ubuntu-20.04-amd64.charm
```

In doing so, the charm will keep any of its previous relations and configurations. However, if you want want to use a different Container Image than the charm has been deployed with, you will have to remove the application first, and add it manually, and then add the necessary configurations:

```bash
juju remove-application finos-waltz-k8s
```

You can see the status by running ``juju status``. After it was removed, redeploy it again, and also specifying the new Container Image as a resource:

```bash
juju deploy ./finos-waltz-k8s_ubuntu-20.04-amd64.charm --resource waltz-image=<another-image>
```

Afterwards, the relation with the ``postgresql-k8s`` charm has to be recreated:

```bash
juju relate finos-waltz-k8s:db postgresql-k8s:db
```

## Destroy setup

To remove Waltz, you can remove the Juju model it was deployed in:

```bash
juju destroy-model -y --destroy-storage waltz-model
```

The bootstrapped Juju controller can be destroyed as well. Doing so will also destroy any and all models it has:

```bash
juju destroy-controller -y --destroy-all-models --destroy-storage waltz-controller
```

To also remove Juju and MicroK8s, you can run:

``` bash
sudo snap remove juju --purge
sudo snap remove microk8s --purge
```
