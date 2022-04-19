[![FINOS - Incubating](https://cdn.jsdelivr.net/gh/finos/contrib-toolbox@master/images/badge-incubating.svg)](https://finosfoundation.atlassian.net/wiki/display/FINOS/Incubating) 

[![Get it from the Charmhub](https://charmhub.io/finos-waltz-k8s/badge.svg)](https://charmhub.io/finos-waltz-k8s)

# A Charmed Operator for Waltz

This is the repository for the Waltz charmed operator, also known as "charm". This can be deployed individually or as a [bundle](https://github.com/finos/waltz-juju-bundle). 

> 💡If you are evaluating Waltz, you should use the whole [bundle](https://github.com/finos/waltz-juju-bundle) instead of this single charm. You should only deploy this charmed operator by itself if you already have a PostgreSQL database.

> 💡 You can find more information about Charmed Operators and Charmed Waltz in the [bundle](https://github.com/finos/waltz-juju-bundle) repository.

## Deploying this Charmed Operator

If you don’t have a Juju model, you can follow [this guide](https://github.com/finos/waltz-juju-bundle/blob/main/docs/guides/LocalDeployment.md) until the point you have one. You can then deploy this single charmed operator (instead of the whole bundle) running

```
juju deploy finos-waltz-k8s
``` 

### Connecting to PostgreSQL

To connect to your already existing PostgreSQL database, you can run
```
juju config finos-waltz-k8s db-host="<db-host>" db-port="<db-port>" db-name="<db-name>" db-username="<db-username>" db-password="<db-password>"
```
## OCI Images

This charm requires the Waltz docker image: ``ghcr.io/finos/waltz``.

## Charm releases

This repository is configured to automatically build and publish a new Charm revision after a Pull Request merges. For more information, see [here](docs/CharmPublishing.md).

## Help and Support

Feel free to [create an issue](https://github.com/finos/waltz-integration-juju/issues/new/choose) or submit a Pull Request to this repository in order to contribute; make sure to read the Waltz [Contribution Guide](https://github.com/finos/waltz/blob/master/CONTRIBUTING.md) first.

You can also use chat to the contributors to this Waltz integration via the [FINOS Waltz Slack Channel](https://finos-lf.slack.com/archives/C01S1D746TW).

## Roadmap

TODO

## Contributing

Visit Waltz [Contribution Guide](https://github.com/finos/waltz/blob/master/CONTRIBUTING.md) to learn how to contribute to Waltz.

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines on enhancements to this charm following best practice guidelines, and `DEVELOPMENT.md` for developer guidance.

## License

Copyright (c) 2021-present, Canonical

Distributed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

SPDX-License-Identifier: [Apache-2.0](https://spdx.org/licenses/Apache-2.0)
