# Copyright 2017 Huawei Technologies Co.,LTD.
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


from mogan.api.validation import parameter_types


create_instance = {
    "type": "object",
    "properties": {
        'name': parameter_types.name,
        'description': parameter_types.description,
        'availability_zone': parameter_types.availability_zone,
        'image_uuid': parameter_types.image_id,
        'instance_type_uuid': parameter_types.instance_type_id,
        'networks': {
            'type': 'array', 'minItems': 1,
            'items': {
                'type': 'object',
                'properties': {
                    'net_id': parameter_types.network_id,
                    'port_type': parameter_types.port_type,
                },
                'required': ['net_id'],
                'additionalProperties': False,
            },
        },
        'extra': parameter_types.extra,
    },
    'required': ['name', 'image_uuid', 'instance_type_uuid', 'networks'],
    'additionalProperties': False,
}