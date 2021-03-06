.. -*- rst -*-

=========
 Flavors
=========

Show and manage server flavors.

Flavors are a way to describe the basic dimensions of a server to be
created including how much ``cpu``, ``ram``, and ``disk space`` are
allocated to a server built with this flavor.

List Flavors
============

.. rest_method:: GET /flavors

Lists all flavors accessible to your project.

Normal response codes: 200

Error response codes: unauthorized(401), forbidden(403)

Response
--------

.. rest_parameters:: parameters.yaml

   - flavors: flavors
   - name: flavor_name
   - links: links
   - description: flavor_description
   - resources: flavor_resources
   - resource_aggregates: flavor_aggregates
   - uuid: flavor_uuid
   - created_at: created_at
   - updated_at: updated_at
   - is_public: flavor_is_public
   - disabled: flavor_disabled

**Example List flavors**

.. literalinclude:: samples/flavors/flavors-list-resp.json
   :language: javascript

Create Flavor
=============

.. rest_method:: POST /flavors

Creates a flavor.

Creating a flavor is typically only available to administrators of a
cloud because this has implications for scheduling efficiently in the cloud.

Normal response codes: 201

Error response codes: badRequest(400), unauthorized(401), forbidden(403),
conflict(409)

Request
-------

.. rest_parameters:: parameters.yaml

   - name: flavor_name
   - description: flavor_description
   - resources: flavor_resources
   - resource_aggregates: flavor_aggregates
   - is_public: flavor_is_public_not_required
   - disabled: flavor_disabled

**Example Create Flavor**

.. literalinclude:: samples/flavors/flavor-create-post-req.json
   :language: javascript

Response
--------

.. rest_parameters:: parameters.yaml

   - name: flavor_name
   - links: links
   - description: flavor_description
   - resources: flavor_resources
   - resource_aggregates: flavor_aggregates
   - uuid: flavor_uuid
   - created_at: created_at
   - updated_at: updated_at
   - is_public: flavor_is_public
   - disabled: flavor_disabled

**Example Create flavor**

.. literalinclude:: samples/flavors/flavor-create-post-resp.json
   :language: javascript

Update Flavor
=============

.. rest_method:: PATCH /flavors/{flavor_uuid}

Updates a flavor.

Updating a flavor is typically only available to administrators of a
cloud because this has implications for scheduling efficiently in the cloud.

Normal response codes: 200

Error response codes: badRequest(400), unauthorized(401), forbidden(403),
conflict(409)

Request
-------

The BODY of the PATCH request must be a JSON PATCH document, adhering to
`RFC 6902 <https://tools.ietf.org/html/rfc6902>`_.

.. rest_parameters:: parameters.yaml

  - flavor_uuid: flavor_uuid_path

**Example Update Flavor: JSON request**

.. literalinclude:: samples/flavors/flavor-update-put-req.json
   :language: javascript

Response
--------

.. rest_parameters:: parameters.yaml

   - name: flavor_name
   - links: links
   - description: flavor_description
   - resources: flavor_resources
   - resource_aggregates: flavor_aggregates
   - uuid: flavor_uuid
   - created_at: created_at
   - updated_at: updated_at
   - is_public: flavor_is_public
   - disabled: flavor_disabled

**Example Update flavor**

.. literalinclude:: samples/flavors/flavor-update-put-resp.json
   :language: javascript

Show Server Flavor Details
==========================

.. rest_method:: GET /flavors/{flavor_uuid}

Shows details for a flavor.

Normal response codes: 200

Error response codes: unauthorized(401), forbidden(403), itemNotFound(404)

Request
-------

.. rest_parameters:: parameters.yaml

  - flavor_uuid: flavor_uuid_path

Response
--------

.. rest_parameters:: parameters.yaml

   - name: flavor_name
   - links: links
   - description: flavor_description
   - resources: flavor_resources
   - resource_aggregates: flavor_aggregates
   - uuid: flavor_uuid
   - created_at: created_at
   - updated_at: updated_at
   - is_public: flavor_is_public
   - disabled: flavor_disabled

**Example Show Flavor Details**

.. literalinclude:: samples/flavors/flavor-get-resp.json
   :language: javascript


Delete Flavor
=============

.. rest_method:: DELETE /flavors/{flavor_uuid}

Deletes a flavor.

This is typically an admin only action. Deleting a flavor that is in use by
existing servers is not recommended as it can cause incorrect data to
be returned to the user under some operations.

Normal response codes: 204

Error response codes: unauthorized(401), forbidden(403), itemNotFound(404)

Request
-------

.. rest_parameters:: parameters.yaml

  - flavor_uuid: flavor_uuid_path

Response
--------

No body content is returned on a successful DELETE.
