# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest
from unittest import mock

from ops import model, testing
from pgsql.opslib.pgsql import client

import charm


class TestCharm(unittest.TestCase):
    def setUp(self):
        # Mock pgsql's leader data getter and setter.
        self.leadership_data = {}
        self._patch(client, "_get_pgsql_leader_data", self.leadership_data.copy)
        self._patch(client, "_set_pgsql_leader_data", self.leadership_data.update)

        self.harness = testing.Harness(charm.WaltzOperatorCharm)
        self.addCleanup(self.harness.cleanup)

    def _patch(self, obj, method, *args, **kwargs):
        """Patches the given method and returns its Mock."""
        patcher = mock.patch.object(obj, method, *args, **kwargs)
        mock_patched = patcher.start()
        self.addCleanup(patcher.stop)

        return mock_patched

    def _add_relation(self, relation_name, relator_name, relation_data):
        """Adds a relation to the charm."""
        relation_id = self.harness.add_relation(relation_name, relator_name)
        self.harness.add_relation_unit(relation_id, "%s/0" % relator_name)

        self.harness.update_relation_data(relation_id, relator_name, relation_data)
        return relation_id

    def test_database_relation(self):
        """Test for the PostgreSQL relation."""
        # Setup mocks and start the initial hooks.
        container = self.harness.model.unit.get_container("waltz")
        mock_stop = self._patch(container, "stop")
        mock_can_connect = self._patch(container, "can_connect")
        mock_can_connect.return_value = True

        # Setting the leader will allow the PostgreSQL charm to write relation data.
        self.harness.set_leader(True)
        self.harness.begin_with_initial_hooks()

        # Join a PostgreSQL charm. A database relation joined is then triggered. The database
        # name should be set in the event.database. Without it, we can't continue on the
        # master changed event.
        rel_id = self._add_relation("db", "postgresql-charm", {})

        # Update the relation data with a PostgreSQL connection string.
        connection_url = "host=foo.lish port=5432 dbname=%s user=someuser password=somepass"
        connection_url = connection_url % self.harness.charm.app.name
        rel_data = {
            "database": self.harness.charm.app.name,
            "master": connection_url,
        }
        self.harness.update_relation_data(rel_id, "postgresql-charm", rel_data)

        # Emit the master changed event.
        relation = self.harness.model.get_relation("db")
        unit = self.harness.charm.unit
        self.harness.charm.db.on.master_changed.emit(relation, self.harness.charm.app, unit, unit)

        # The Pebble plan should be updated with the PostgreSQL connection data from the relation.
        database_config = dict([pair.split("=") for pair in connection_url.split()])
        self._check_pebble_plan(database_config)

        # Remove the relation, and check that the charm is now in BlockedStatus and that the
        # container was stopped.
        self.harness.remove_relation(rel_id)

        self.assertIsInstance(self.harness.model.unit.status, model.BlockedStatus)
        mock_stop.assert_called_with("waltz")

    def test_waltz_pebble_ready(self):
        # Check the initial Pebble plan is empty
        initial_plan = self.harness.get_container_pebble_plan("waltz")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")

        # Get the waltz container from the model and emit the PebbleReadyEvent carrying it.
        # We can't connect to the container yet.
        container = self.harness.model.unit.get_container("waltz")
        mock_can_connect = self._patch(container, "can_connect")
        mock_can_connect.return_value = False

        self.harness.set_leader(True)
        self.harness.begin_with_initial_hooks()
        self.harness.charm.on.waltz_pebble_ready.emit(container)
        self.assertIsInstance(self.harness.model.unit.status, model.WaitingStatus)

        # Reemit the PebbleReadyEvent, and the container can be connected to, but we don't have
        # a database connection.
        mock_stop = self._patch(container, "stop")
        mock_can_connect.return_value = True
        self.harness.charm.on.waltz_pebble_ready.emit(container)
        self.assertIsInstance(self.harness.model.unit.status, model.BlockedStatus)

        # The service was not defined yet, as we did not have any database.
        mock_stop.assert_not_called()

        # Add a database relation, and expect it to become active.
        connection_url = "host=foo.lish port=5432 dbname=%s user=someuser password=somepass"
        connection_url = connection_url % self.harness.charm.app.name
        rel_data = {
            "database": self.harness.charm.app.name,
            "master": connection_url,
        }
        rel_id = self._add_relation("db", "postgresql-charm", rel_data)

        # Check the service was started
        service = self.harness.model.unit.get_container("waltz").get_service("waltz")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, model.ActiveStatus())

        # Check that we've got the plan we expected.
        database_config = dict([pair.split("=") for pair in connection_url.split()])
        self._check_pebble_plan(database_config)

        # Emit the Pebble ready again, make sure that the container is NOT restarted if
        # there was no configuration change.
        mock_restart = self._patch(container, "restart")
        self.harness.charm.on.waltz_pebble_ready.emit(container)
        mock_restart.assert_not_called()

    def _check_pebble_plan(self, expected_config):
        updated_plan = self.harness.get_container_pebble_plan("waltz").to_dict()
        expected_plan = {
            "services": {
                "waltz": {
                    "override": "replace",
                    "summary": "waltz",
                    "command": "/bin/sh -c 'docker-entrypoint.sh update run'",
                    "startup": "enabled",
                    "user": "waltz",
                    "environment": {
                        "DB_HOST": expected_config["host"],
                        "DB_PORT": expected_config["port"],
                        "DB_NAME": expected_config["dbname"],
                        "DB_USER": expected_config["user"],
                        "DB_PASSWORD": expected_config["password"],
                        "DB_SCHEME": "waltz",
                        "WALTZ_FROM_EMAIL": "help@finos.org",
                        "CHANGELOG_FILE": "/opt/waltz/liquibase/db.changelog-master.xml",
                    },
                }
            },
        }
        self.assertDictEqual(expected_plan, updated_plan)
