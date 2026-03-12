from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
    name: timeweb
    plugin_type: inventory
    short_description: Timeweb Cloud inventory source
    requirements:
      - requests
    description:
      - Get inventory hosts from Timeweb Cloud API.
    options:
      plugin:
        description: The name of this plugin, it should always be set to C(mitmx.timeweb.timeweb)
        required: true
        choices: ['mitmx.timeweb.timeweb']
      api_token:
        description: Timeweb Cloud API token
        env:
          - name: TIMEWEB_TOKEN
        required: true
        type: string
      api_endpoint:
        description: Timeweb API endpoint
        type: string
        default: https://api.timeweb.cloud
      validate_certs:
        description: Validate SSL certificates
        type: boolean
        default: true
      keyed_groups:
        description:
          - Add hosts to group based on the values of a host variable
        type: list
        elements: dict
        default: []
      groups:
        description:
          - Add hosts to group based on Jinja2 conditionals
        type: dict
        default: {}
      compose:
        description:
          - Set hostvars from Jinja2 expressions
        type: dict
        default: {}
'''

import requests
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable
from ansible.errors import AnsibleParserError


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    NAME = 'mitmx.timeweb.timeweb'

    def verify_file(self, path):
        """Return true/false if this is a valid file for this plugin to consume"""
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('timeweb.yml', 'timeweb.yaml')):
                return True
        return False

    def parse(self, inventory, loader, path, cache=True):
        """Parses the inventory file"""
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path)

        api_token = self.get_option('api_token')
        api_endpoint = self.get_option('api_endpoint').rstrip('/')
        validate_certs = self.get_option('validate_certs')

        if not api_token:
            raise AnsibleParserError("Timeweb API token must be provided via 'api_token' or TIMEWEB_TOKEN env var")

        cache_key = self.get_cache_key(path)

        if cache:
            try:
                data = self._cache[cache_key]
                if data:
                    self._populate_from_data(data)
                    return
            except KeyError:
                pass

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.get(f"{api_endpoint}/api/v1/servers", headers=headers, verify=validate_certs)
            resp.raise_for_status()
            servers = resp.json().get("servers", [])
        except requests.RequestException as e:
            raise AnsibleParserError(f"Error fetching servers from Timeweb API: {e}")

        # Transform into Ansible inventory
        inventory_data = []
        for srv in servers:
            host_name = srv.get("name") or srv.get("id")
            host_ip = self._get_main_ipv4(srv)

            if not host_name or not host_ip:
                continue

            host_vars = {
                "ansible_host": host_ip,
                "id": srv.get("id"),
                "status": srv.get("status"),
                "location": srv.get("location"),
                "availability_zone": srv.get("availability_zone"),
                "comment": srv.get("comment"),
                "project_id": srv.get("project_id"),
                "ram": srv.get("ram"),
                "cpu": srv.get("cpu"),
            }

            inventory_data.append((host_name, host_vars))

        # Populate inventory
        for host_name, host_vars in inventory_data:
            self.inventory.add_host(host_name)
            for var, value in host_vars.items():
                self.inventory.set_variable(host_name, var, value)

            self._set_composite_vars(self.get_option('compose'), host_vars, host_name, strict=False)
            self._add_host_to_keyed_groups(self.get_option('keyed_groups'), host_vars, host_name)
            self._add_host_to_composed_groups(self.get_option('groups'), host_vars, host_name)

        if cache:
            self._cache[cache_key] = inventory_data

    def _populate_from_data(self, data):
        """Populate inventory from cached data"""
        for host_name, host_vars in data:
            self.inventory.add_host(host_name)
            for var, value in host_vars.items():
                self.inventory.set_variable(host_name, var, value)

    def _get_main_ipv4(self, srv):
        for net in srv.get("networks", []):
            if net.get("type") == "public":
                for ip_info in net.get("ips", []):
                    if ip_info.get("type") == "ipv4" and ip_info.get("is_main"):
                        return ip_info.get("ip")
        return None
