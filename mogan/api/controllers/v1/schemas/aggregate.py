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


create_aggregate = {
    "type": "object",
    "properties": {
        'name': parameter_types.name,
        'metadata': parameter_types.metadata,
    },
    'required': ['name'],
    'additionalProperties': False,
}

add_aggregate_node = {
    'type': 'object',
    'properties': {
        'node': parameter_types.name,
    },
    'required': ['node'],
    'additionalProperties': False,
}
