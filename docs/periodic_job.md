# FINOS Waltz Juju EC2 deployment - Periodic refresh

The [Refresh EC2 FINOS Waltz deployment](../.github/workflows/refresh_deployment.yaml) job will run periodically for a configured Juju EC2 deployment and will refresh the Waltz and Ingress charms to their latest revision. This job requires a few Secrets to be defined in the project repository (`Settings > Secrets > Actions > Repository secrets` or using the `gh secret set` command):

- `SSH_USER`: The username to use when connecting to the EC2 instance.
- `SSH_HOST`: The hostname of the EC2 instance.
- `SSH_KEY`: The private SSH key to use when connecting to the EC2 instance.

Once the above repository secrets have been set, the job should succeed. A manual job can also be triggered by going to `Actions > Refresh EC2 FINOS Waltz deployment > Run workflow`.

The Github CLI commands for setting the secrets are:

```bash
gh -R finos/waltz-integration-juju secret set SSH_USER
gh -R finos/waltz-integration-juju secret set SSH_HOST
gh -R finos/waltz-integration-juju secret set SSH_KEY < ~/.ssh/id_rsa
```

The CLI will prompt you to paste the `SSH_USER` and `SSH_HOST` secrets in the terminal, while `SSH_KEY` will load the private key from the specified location.

Next, the public SSH key will have to be copied over to the Instance that will run the Waltz deployment. This can be done by simply running:

```bash
ssh-copy-id user@remote-host
```
