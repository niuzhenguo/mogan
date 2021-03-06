# Copyright 2016 Huawei Technologies Co.,LTD.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Unit tests for engine API."""

import mock
from oslo_context import context

from mogan.common import exception
from mogan.common import states
from mogan.engine import api as engine_api
from mogan.engine import rpcapi as engine_rpcapi
from mogan import objects
from mogan.tests.unit.db import base
from mogan.tests.unit.db import utils as db_utils


class ComputeAPIUnitTest(base.DbTestCase):
    def setUp(self):
        super(ComputeAPIUnitTest, self).setUp()
        self.user_id = 'fake-user'
        self.project_id = 'fake-project'
        self.engine_api = engine_api.API()
        self.context = context.RequestContext(user=self.user_id,
                                              tenant=self.project_id)

    def _create_flavor(self):
        flavor = db_utils.get_test_flavor()
        flavor['extra'] = {}
        type_obj = objects.Flavor(self.context, **flavor)
        type_obj.create(self.context)
        return type_obj

    @mock.patch('mogan.engine.api.API._check_requested_networks')
    def test__validate_and_build_base_options(self, mock_check_nets):
        flavor = self._create_flavor()
        mock_check_nets.return_value = 3

        base_opts, max_network_count, key_pair = \
            self.engine_api._validate_and_build_base_options(
                self.context,
                flavor=flavor,
                image_uuid='fake-uuid',
                name='fake-name',
                description='fake-descritpion',
                availability_zone='test_az',
                metadata={'k1', 'v1'},
                requested_networks=None,
                user_data=None,
                key_name=None,
                max_count=2,
                partitions={'root_gb': 100})

        self.assertEqual('fake-user', base_opts['user_id'])
        self.assertEqual('fake-project', base_opts['project_id'])
        self.assertEqual(states.BUILDING, base_opts['status'])
        self.assertEqual(flavor.uuid, base_opts['flavor_uuid'])
        self.assertEqual({'k1', 'v1'}, base_opts['metadata'])
        self.assertEqual('test_az', base_opts['availability_zone'])
        self.assertIsNone(key_pair)

    @mock.patch('mogan.network.api.get_client')
    def test__check_requested_networks(self, mock_get_client):
        mock_get_client.return_value = mock.MagicMock()
        mock_get_client.return_value.list_networks.return_value = \
            {'networks': [{'id': '1', 'subnets': {'id': '2'}},
                          {'id': '3', 'subnets': {'id': '4'}}]}
        mock_get_client.return_value.list_ports.return_value = \
            {'ports': [{'id': '5',
                        'fixed_ips': [{'ip_address': '192.168.1.1'}]},
                       {'id': '6',
                        'fixed_ips': [{'ip_address': '192.168.1.2'}]}]}
        mock_get_client.return_value.show_quota.return_value = \
            {'quota': {'port': 10}}

        requested_networks = [{'net_id': '1'}, {'net_id': '3'},
                              {'port_id': '5'}, {'port_id': '6'}]
        max_network_count = self.engine_api._check_requested_networks(
            self.context, requested_networks=requested_networks, max_count=2)

        self.assertEqual(2, max_network_count)

    @mock.patch.object(objects.Server, 'create')
    def test__provision_servers(self, mock_server_create):
        mock_server_create.return_value = mock.MagicMock()

        base_options = {'image_uuid': 'fake-uuid',
                        'status': states.BUILDING,
                        'user_id': 'fake-user',
                        'project_id': 'fake-project',
                        'flavor_uuid': 'fake-type-uuid',
                        'name': 'fake-name',
                        'description': 'fake-description',
                        'extra': {},
                        'availability_zone': None}
        min_count = 1
        max_count = 2
        self.engine_api._provision_servers(self.context, base_options,
                                           min_count, max_count,
                                           server_group=None)
        calls = [mock.call() for i in range(max_count)]
        mock_server_create.assert_has_calls(calls)

    @mock.patch('mogan.scheduler.rpcapi.SchedulerAPI.select_destinations')
    @mock.patch.object(engine_rpcapi.EngineAPI, 'schedule_and_create_servers')
    @mock.patch('mogan.engine.api.API._get_image')
    @mock.patch('mogan.engine.api.API._validate_and_build_base_options')
    @mock.patch('mogan.engine.api.API.list_availability_zones')
    def test_create(self, mock_list_az, mock_validate, mock_get_image,
                    mock_create, mock_select_dest):
        flavor = self._create_flavor()
        base_options = {'image_uuid': 'fake-uuid',
                        'status': states.BUILDING,
                        'user_id': 'fake-user',
                        'project_id': 'fake-project',
                        'flavor_uuid': 'fake-type-uuid',
                        'name': 'fake-name',
                        'description': 'fake-description',
                        'metadata': {'k1', 'v1'},
                        'availability_zone': 'test_az'}
        min_count = 1
        max_count = 2
        mock_validate.return_value = (base_options, max_count, None)
        mock_get_image.return_value = {'status': 'active'}
        mock_create.return_value = mock.MagicMock()
        mock_list_az.return_value = {'availability_zones': ['test_az']}
        mock_select_dest.return_value = \
            [mock.MagicMock() for i in range(max_count)]
        requested_networks = [{'uuid': 'fake'}]

        res = self.dbapi._get_quota_usages(self.context, self.project_id)
        before_in_use = 0
        if res.get('servers') is not None:
            before_in_use = res.get('servers').in_use

        self.engine_api.create(
            self.context,
            flavor=flavor,
            image_uuid='fake-uuid',
            name='fake-name',
            description='fake-descritpion',
            availability_zone='test_az',
            metadata={'k1', 'v1'},
            requested_networks=requested_networks,
            min_count=min_count,
            max_count=max_count)

        mock_list_az.assert_called_once_with(self.context)
        mock_validate.assert_called_once_with(
            self.context, flavor, 'fake-uuid', 'fake-name',
            'fake-descritpion', 'test_az', {'k1', 'v1'}, requested_networks,
            None, None, max_count, None)
        self.assertTrue(mock_create.called)
        self.assertTrue(mock_get_image.called)
        res = self.dbapi._get_quota_usages(self.context, self.project_id)
        after_in_use = res.get('servers').in_use
        self.assertEqual(before_in_use + 2, after_in_use)

    @mock.patch('mogan.engine.api.API.list_availability_zones')
    def test_create_with_invalid_az(self, mock_list_az):
        flavor = mock.MagicMock()
        mock_list_az.return_value = {'availability_zones': ['invalid_az']}

        self.assertRaises(
            exception.AZNotFound,
            self.engine_api.create,
            self.context,
            flavor,
            'fake-uuid',
            'fake-name',
            'fake-descritpion',
            'test_az',
            {'k1', 'v1'},
            [{'uuid': 'fake'}])

        mock_list_az.assert_called_once_with(self.context)

    @mock.patch('mogan.engine.api.API._get_image')
    @mock.patch('mogan.engine.api.API._validate_and_build_base_options')
    @mock.patch('mogan.engine.api.API.list_availability_zones')
    def test_create_over_quota_limit(self, mock_list_az, mock_validate,
                                     mock_get_image):
        flavor = self._create_flavor()

        base_options = {'image_uuid': 'fake-uuid',
                        'status': states.BUILDING,
                        'user_id': 'fake-user',
                        'project_id': 'fake-project',
                        'flavor_uuid': 'fake-type-uuid',
                        'name': 'fake-name',
                        'description': 'fake-description',
                        'metadata': {'k1', 'v1'},
                        'availability_zone': 'test_az'}
        min_count = 11
        max_count = 20
        mock_validate.return_value = (base_options, max_count, None)
        mock_get_image.return_value = {'status': 'active'}
        mock_list_az.return_value = {'availability_zones': ['test_az']}
        requested_networks = [{'uuid': 'fake'}]

        self.assertRaises(
            exception.OverQuota,
            self.engine_api.create,
            self.context,
            flavor,
            'fake-uuid',
            'fake-name',
            'fake-descritpion',
            'test_az',
            {'k1', 'v1'},
            requested_networks,
            None,
            None,
            None,
            min_count,
            max_count)

    def _create_fake_server_obj(self, fake_server):
        fake_server_obj = objects.Server(self.context, **fake_server)
        fake_server_obj.create(self.context)
        return fake_server_obj

    def test_lock_by_owner(self):
        fake_server = db_utils.get_test_server(
            user_id=self.user_id, project_id=self.project_id)
        fake_server_obj = self._create_fake_server_obj(fake_server)
        self.engine_api.lock(self.context, fake_server_obj)
        self.assertTrue(fake_server_obj.locked)
        self.assertEqual('owner', fake_server_obj.locked_by)

    def test_unlock_by_owner(self):
        fake_server = db_utils.get_test_server(
            user_id=self.user_id, project_id=self.project_id,
            locked=True, locked_by='owner')
        fake_server_obj = self._create_fake_server_obj(fake_server)
        self.engine_api.unlock(self.context, fake_server_obj)
        self.assertFalse(fake_server_obj.locked)
        self.assertIsNone(fake_server_obj.locked_by)

    def test_lock_by_admin(self):
        fake_server = db_utils.get_test_server(
            user_id=self.user_id, project_id=self.project_id)
        fake_server_obj = self._create_fake_server_obj(fake_server)
        admin_context = context.get_admin_context()
        self.engine_api.lock(admin_context, fake_server_obj)
        self.assertTrue(fake_server_obj.locked)
        self.assertEqual('admin', fake_server_obj.locked_by)

    def test_unlock_by_admin(self):
        fake_server = db_utils.get_test_server(
            user_id=self.user_id, project_id=self.project_id,
            locked=True, locked_by='owner')
        fake_server_obj = self._create_fake_server_obj(fake_server)
        admin_context = context.get_admin_context()
        self.engine_api.unlock(admin_context, fake_server_obj)
        self.assertFalse(fake_server_obj.locked)
        self.assertIsNone(fake_server_obj.locked_by)

    @mock.patch('mogan.engine.api.API._delete_server')
    def test_delete_locked_server_with_non_admin(self, mock_deleted):
        fake_server = db_utils.get_test_server(
            user_id=self.user_id, project_id=self.project_id,
            locked=True, locked_by='owner')
        fake_server_obj = self._create_fake_server_obj(fake_server)
        self.assertRaises(exception.ServerIsLocked,
                          self.engine_api.delete,
                          self.context, fake_server_obj)
        mock_deleted.assert_not_called()

    @mock.patch.object(engine_rpcapi.EngineAPI, 'set_power_state')
    def test_power_locked_server_with_non_admin(self, mock_powered):
        fake_server = db_utils.get_test_server(
            user_id=self.user_id, project_id=self.project_id,
            locked=True, locked_by='owner')
        fake_server_obj = self._create_fake_server_obj(fake_server)
        self.assertRaises(exception.ServerIsLocked,
                          self.engine_api.power,
                          self.context, fake_server_obj, 'reboot')
        mock_powered.assert_not_called()

    @mock.patch('mogan.engine.api.API._delete_server')
    def test_delete_locked_server_with_admin(self, mock_deleted):
        fake_server = db_utils.get_test_server(
            user_id=self.user_id, project_id=self.project_id,
            locked=True, locked_by='owner')
        fake_server_obj = self._create_fake_server_obj(fake_server)
        admin_context = context.get_admin_context()
        self.engine_api.delete(admin_context, fake_server_obj)
        self.assertTrue(mock_deleted.called)

    @mock.patch.object(engine_rpcapi.EngineAPI, 'set_power_state')
    def test_power_locked_server_with_admin(self, mock_powered):
        fake_server = db_utils.get_test_server(
            user_id=self.user_id, project_id=self.project_id,
            locked=True, locked_by='owner')
        fake_server_obj = self._create_fake_server_obj(fake_server)
        admin_context = context.get_admin_context()
        self.engine_api.power(admin_context, fake_server_obj, 'reboot')
        self.assertTrue(mock_powered.called)

    @mock.patch.object(engine_rpcapi.EngineAPI, 'rebuild_server')
    def test_rebuild_locked_server_with_non_admin(self, mock_rebuild):
        fake_server = db_utils.get_test_server(
            user_id=self.user_id, project_id=self.project_id,
            locked=True, locked_by='owner')
        fake_server_obj = self._create_fake_server_obj(fake_server)
        self.assertRaises(exception.ServerIsLocked,
                          self.engine_api.rebuild,
                          self.context, fake_server_obj)
        mock_rebuild.assert_not_called()

    @mock.patch.object(engine_rpcapi.EngineAPI, 'rebuild_server')
    @mock.patch('mogan.engine.api.API._get_image')
    def test_rebuild_locked_server_with_admin(self, mock_rebuild,
                                              mock_get_image):
        fake_server = db_utils.get_test_server(
            user_id=self.user_id, project_id=self.project_id,
            locked=True, locked_by='owner')
        fake_server_obj = self._create_fake_server_obj(fake_server)
        admin_context = context.get_admin_context()
        mock_get_image.side_effect = None
        self.engine_api.rebuild(admin_context, fake_server_obj)
        self.assertTrue(mock_rebuild.called)

    @mock.patch.object(engine_rpcapi.EngineAPI, 'rebuild_server')
    @mock.patch('mogan.engine.api.API._get_image')
    def test_rebuild_server(self, mock_rebuild, mock_get_image):
        fake_server = db_utils.get_test_server(
            user_id=self.user_id, project_id=self.project_id)
        fake_server_obj = self._create_fake_server_obj(fake_server)
        mock_get_image.side_effect = None
        self.engine_api.rebuild(self.context, fake_server_obj)
        self.assertTrue(mock_get_image.called)
        self.assertTrue(mock_rebuild.called)

    @mock.patch.object(engine_rpcapi.EngineAPI, 'rebuild_server')
    @mock.patch('mogan.engine.api.API._get_image')
    def test_rebuild_server_with_new_image(self, mock_rebuild, mock_get_image):
        fake_server = db_utils.get_test_server(
            user_id=self.user_id, project_id=self.project_id)
        fake_server_obj = self._create_fake_server_obj(fake_server)
        mock_get_image.side_effect = None
        image_uuid = 'fake-uuid'

        self.engine_api.rebuild(self.context, fake_server_obj, image_uuid)
        self.assertTrue(mock_get_image.called)
        self.assertTrue(mock_rebuild.called)

    @mock.patch.object(engine_rpcapi.EngineAPI, 'detach_interface')
    def test_detach_interface(self, mock_detach_interface):
        fake_server = db_utils.get_test_server(
            user_id=self.user_id, project_id=self.project_id)
        fake_server_obj = self._create_fake_server_obj(fake_server)
        self.engine_api.detach_interface(self.context, fake_server_obj,
                                         fake_server_obj['nics'][0]['port_id'])
        self.assertTrue(mock_detach_interface.called)

    def test_create_key_pairs_with_quota(self):
        res = self.dbapi._get_quota_usages(self.context, self.project_id)
        before_in_use = 0
        if res.get('keypairs') is not None:
            before_in_use = res.get('keypairs').in_use
        self.engine_api.create_key_pair(self.context, self.user_id,
                                        'test_keypair')
        res = self.dbapi._get_quota_usages(self.context, self.project_id)
        after_in_use = res.get('keypairs').in_use
        self.assertEqual(before_in_use + 1, after_in_use)

    def test_create_key_pairs_with_over_quota_limit(self):
        self.config(keypairs_hard_limit=1, group='quota')
        res = self.dbapi._get_quota_usages(self.context, self.project_id)
        before_in_use = 0
        if res.get('keypairs') is not None:
            before_in_use = res.get('keypairs').in_use
        self.engine_api.create_key_pair(self.context, self.user_id,
                                        'test_keypair')
        res = self.dbapi._get_quota_usages(self.context, self.project_id)
        after_in_use = res.get('keypairs').in_use
        self.assertEqual(before_in_use + 1, after_in_use)
        self.assertRaises(
            exception.OverQuota,
            self.engine_api.create_key_pair,
            self.context,
            self.user_id,
            'test_keypair')

    @mock.patch.object(engine_rpcapi.EngineAPI, 'manage_server')
    @mock.patch.object(engine_api.API, '_check_num_servers_quota')
    def test_manage(self, check_quota_mock, mock_manage_server):
        node_uuid = 'aacdbd78-d670-409e-95aa-ecfcfb94fee2'
        mock_manage_server.return_value = mock.MagicMock()

        res = self.dbapi._get_quota_usages(self.context, self.project_id)
        before_in_use = 0
        if res.get('servers') is not None:
            before_in_use = res.get('servers').in_use

        self.engine_api.manage(self.context,
                               node_uuid=node_uuid,
                               name='fake-name',
                               description='fake-descritpion',
                               metadata={'k1', 'v1'})

        check_quota_mock.assert_called_once_with(self.context, 1, 1)
        self.assertTrue(mock_manage_server.called)
        res = self.dbapi._get_quota_usages(self.context, self.project_id)
        after_in_use = res.get('servers').in_use
        self.assertEqual(before_in_use + 1, after_in_use)
