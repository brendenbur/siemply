"""
Siemply Inventory - Host and group management
"""

import logging
import yaml
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import os


@dataclass
class Host:
    """Represents a single host in the inventory"""
    name: str
    ansible_host: str
    ansible_user: str
    ansible_port: int = 22
    ansible_ssh_private_key_file: Optional[str] = None
    splunk_type: Optional[str] = None
    splunk_version: Optional[str] = None
    os_family: Optional[str] = None
    os_version: Optional[str] = None
    cpu_arch: Optional[str] = None
    memory_gb: Optional[int] = None
    disk_gb: Optional[int] = None
    variables: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}


@dataclass
class Group:
    """Represents a group of hosts in the inventory"""
    name: str
    hosts: List[Host]
    children: List['Group'] = None
    variables: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.variables is None:
            self.variables = {}


class Inventory:
    """
    Inventory management for hosts and groups
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.logger = logging.getLogger(__name__)
        
        # Inventory data
        self.hosts: Dict[str, Host] = {}
        self.groups: Dict[str, Group] = {}
        self.all_hosts: List[Host] = []
        
        # Inventory file path
        self.inventory_file = os.path.join(config_dir, "inventory.yml")
    
    async def load(self, inventory_file: Optional[str] = None):
        """
        Load inventory from YAML file
        
        Args:
            inventory_file: Path to inventory file (optional)
        """
        if inventory_file:
            self.inventory_file = inventory_file
        
        if not os.path.exists(self.inventory_file):
            self.logger.warning(f"Inventory file not found: {self.inventory_file}")
            return
        
        try:
            with open(self.inventory_file, 'r') as f:
                inventory_data = yaml.safe_load(f)
            
            # Parse inventory data
            await self._parse_inventory(inventory_data)
            
            self.logger.info(f"Inventory loaded: {len(self.hosts)} hosts, {len(self.groups)} groups")
            
        except Exception as e:
            self.logger.error(f"Failed to load inventory: {e}")
            raise
    
    async def _parse_inventory(self, inventory_data: Dict[str, Any]):
        """Parse inventory data from YAML"""
        # Get all hosts from inventory
        all_hosts_data = inventory_data.get('all', {})
        
        # Parse hosts and groups recursively
        await self._parse_group('all', all_hosts_data, None)
        
        # Build flat list of all hosts
        self.all_hosts = list(self.hosts.values())
    
    async def _parse_group(self, group_name: str, group_data: Dict[str, Any], parent_group: Optional[Group]):
        """Parse a group and its children"""
        # Create group
        group = Group(name=group_name, hosts=[], children=[], variables={})
        
        # Parse hosts in this group
        hosts_data = group_data.get('hosts', {})
        for host_name, host_data in hosts_data.items():
            host = await self._parse_host(host_name, host_data)
            group.hosts.append(host)
            self.hosts[host_name] = host
        
        # Parse child groups
        children_data = group_data.get('children', {})
        for child_name, child_data in children_data.items():
            child_group = await self._parse_group(child_name, child_data, group)
            group.children.append(child_group)
            self.groups[child_name] = child_group
        
        # Parse group variables
        group.variables = group_data.get('vars', {})
        
        # Store group
        self.groups[group_name] = group
        
        return group
    
    async def _parse_host(self, host_name: str, host_data: Dict[str, Any]) -> Host:
        """Parse a single host"""
        # Extract basic connection info
        ansible_host = host_data.get('ansible_host', host_name)
        ansible_user = host_data.get('ansible_user', 'root')
        ansible_port = host_data.get('ansible_port', 22)
        ansible_ssh_private_key_file = host_data.get('ansible_ssh_private_key_file')
        
        # Extract Splunk-specific info
        splunk_type = host_data.get('splunk_type')
        splunk_version = host_data.get('splunk_version')
        
        # Extract OS info
        os_family = host_data.get('os_family')
        os_version = host_data.get('os_version')
        cpu_arch = host_data.get('cpu_arch')
        
        # Extract resource info
        memory_gb = host_data.get('memory_gb')
        disk_gb = host_data.get('disk_gb')
        
        # Extract other variables
        variables = {k: v for k, v in host_data.items() 
                    if k not in ['ansible_host', 'ansible_user', 'ansible_port', 
                               'ansible_ssh_private_key_file', 'splunk_type', 
                               'splunk_version', 'os_family', 'os_version', 
                               'cpu_arch', 'memory_gb', 'disk_gb']}
        
        return Host(
            name=host_name,
            ansible_host=ansible_host,
            ansible_user=ansible_user,
            ansible_port=ansible_port,
            ansible_ssh_private_key_file=ansible_ssh_private_key_file,
            splunk_type=splunk_type,
            splunk_version=splunk_version,
            os_family=os_family,
            os_version=os_version,
            cpu_arch=cpu_arch,
            memory_gb=memory_gb,
            disk_gb=disk_gb,
            variables=variables
        )
    
    def get_host(self, host_name: str) -> Optional[Host]:
        """Get host by name"""
        return self.hosts.get(host_name)
    
    def get_group(self, group_name: str) -> Optional[Group]:
        """Get group by name"""
        return self.groups.get(group_name)
    
    def get_group_hosts(self, group_name: str) -> List[Host]:
        """Get all hosts in a group (including child groups)"""
        group = self.get_group(group_name)
        if not group:
            return []
        
        hosts = list(group.hosts)
        
        # Add hosts from child groups
        for child_group in group.children:
            hosts.extend(self.get_group_hosts(child_group.name))
        
        return hosts
    
    def get_all_hosts(self) -> List[Host]:
        """Get all hosts in inventory"""
        return self.all_hosts
    
    def get_hosts_by_splunk_type(self, splunk_type: str) -> List[Host]:
        """Get hosts by Splunk type (uf, enterprise)"""
        return [host for host in self.all_hosts if host.splunk_type == splunk_type]
    
    def get_hosts_by_os_family(self, os_family: str) -> List[Host]:
        """Get hosts by OS family"""
        return [host for host in self.all_hosts if host.os_family == os_family]
    
    def get_hosts_by_group_pattern(self, pattern: str) -> List[Host]:
        """Get hosts by group name pattern"""
        hosts = []
        for group_name, group in self.groups.items():
            if pattern in group_name:
                hosts.extend(group.hosts)
        return hosts
    
    def add_host(self, host: Host) -> bool:
        """Add a host to inventory"""
        try:
            self.hosts[host.name] = host
            self.all_hosts.append(host)
            self.logger.info(f"Host added: {host.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add host {host.name}: {e}")
            return False
    
    def remove_host(self, host_name: str) -> bool:
        """Remove a host from inventory"""
        try:
            if host_name in self.hosts:
                host = self.hosts[host_name]
                del self.hosts[host_name]
                self.all_hosts.remove(host)
                self.logger.info(f"Host removed: {host_name}")
                return True
            else:
                self.logger.warning(f"Host not found: {host_name}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to remove host {host_name}: {e}")
            return False
    
    def update_host(self, host_name: str, updates: Dict[str, Any]) -> bool:
        """Update host information"""
        try:
            if host_name not in self.hosts:
                self.logger.warning(f"Host not found: {host_name}")
                return False
            
            host = self.hosts[host_name]
            
            # Update host attributes
            for key, value in updates.items():
                if hasattr(host, key):
                    setattr(host, key, value)
                else:
                    host.variables[key] = value
            
            self.logger.info(f"Host updated: {host_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update host {host_name}: {e}")
            return False
    
    def add_group(self, group: Group) -> bool:
        """Add a group to inventory"""
        try:
            self.groups[group.name] = group
            self.logger.info(f"Group added: {group.name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add group {group.name}: {e}")
            return False
    
    def remove_group(self, group_name: str) -> bool:
        """Remove a group from inventory"""
        try:
            if group_name in self.groups:
                del self.groups[group_name]
                self.logger.info(f"Group removed: {group_name}")
                return True
            else:
                self.logger.warning(f"Group not found: {group_name}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to remove group {group_name}: {e}")
            return False
    
    async def save(self, inventory_file: Optional[str] = None):
        """Save inventory to YAML file"""
        if inventory_file:
            self.inventory_file = inventory_file
        
        try:
            # Convert inventory to YAML format
            inventory_data = await self._to_yaml_format()
            
            # Write to file
            with open(self.inventory_file, 'w') as f:
                yaml.dump(inventory_data, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Inventory saved: {self.inventory_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save inventory: {e}")
            raise
    
    async def _to_yaml_format(self) -> Dict[str, Any]:
        """Convert inventory to YAML format"""
        inventory_data = {'all': {'children': {}}}
        
        # Add groups
        for group_name, group in self.groups.items():
            if group_name == 'all':
                continue
            
            group_data = {
                'hosts': {},
                'vars': group.variables
            }
            
            # Add hosts to group
            for host in group.hosts:
                host_data = {
                    'ansible_host': host.ansible_host,
                    'ansible_user': host.ansible_user,
                    'ansible_port': host.ansible_port,
                    'ansible_ssh_private_key_file': host.ansible_ssh_private_key_file,
                    'splunk_type': host.splunk_type,
                    'splunk_version': host.splunk_version,
                    'os_family': host.os_family,
                    'os_version': host.os_version,
                    'cpu_arch': host.cpu_arch,
                    'memory_gb': host.memory_gb,
                    'disk_gb': host.disk_gb,
                    **host.variables
                }
                group_data['hosts'][host.name] = host_data
            
            # Add child groups
            if group.children:
                group_data['children'] = {}
                for child_group in group.children:
                    group_data['children'][child_group.name] = await self._group_to_yaml(child_group)
            
            inventory_data['all']['children'][group_name] = group_data
        
        return inventory_data
    
    async def _group_to_yaml(self, group: Group) -> Dict[str, Any]:
        """Convert a group to YAML format"""
        group_data = {
            'hosts': {},
            'vars': group.variables
        }
        
        # Add hosts to group
        for host in group.hosts:
            host_data = {
                'ansible_host': host.ansible_host,
                'ansible_user': host.ansible_user,
                'ansible_port': host.ansible_port,
                'ansible_ssh_private_key_file': host.ansible_ssh_private_key_file,
                'splunk_type': host.splunk_type,
                'splunk_version': host.splunk_version,
                'os_family': host.os_family,
                'os_version': host.os_version,
                'cpu_arch': host.cpu_arch,
                'memory_gb': host.memory_gb,
                'disk_gb': host.disk_gb,
                **host.variables
            }
            group_data['hosts'][host.name] = host_data
        
        # Add child groups
        if group.children:
            group_data['children'] = {}
            for child_group in group.children:
                group_data['children'][child_group.name] = await self._group_to_yaml(child_group)
        
        return group_data
    
    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get inventory summary statistics"""
        summary = {
            'total_hosts': len(self.all_hosts),
            'total_groups': len(self.groups),
            'hosts_by_splunk_type': {},
            'hosts_by_os_family': {},
            'hosts_by_group': {}
        }
        
        # Count by Splunk type
        for host in self.all_hosts:
            splunk_type = host.splunk_type or 'unknown'
            summary['hosts_by_splunk_type'][splunk_type] = summary['hosts_by_splunk_type'].get(splunk_type, 0) + 1
        
        # Count by OS family
        for host in self.all_hosts:
            os_family = host.os_family or 'unknown'
            summary['hosts_by_os_family'][os_family] = summary['hosts_by_os_family'].get(os_family, 0) + 1
        
        # Count by group
        for group_name, group in self.groups.items():
            summary['hosts_by_group'][group_name] = len(group.hosts)
        
        return summary
    
    def validate_inventory(self) -> List[str]:
        """Validate inventory for common issues"""
        issues = []
        
        # Check for duplicate host names
        host_names = [host.name for host in self.all_hosts]
        if len(host_names) != len(set(host_names)):
            issues.append("Duplicate host names found")
        
        # Check for missing connection info
        for host in self.all_hosts:
            if not host.ansible_host:
                issues.append(f"Host {host.name} missing ansible_host")
            if not host.ansible_user:
                issues.append(f"Host {host.name} missing ansible_user")
            if not host.ansible_ssh_private_key_file:
                issues.append(f"Host {host.name} missing SSH private key file")
        
        # Check for missing Splunk info
        for host in self.all_hosts:
            if not host.splunk_type:
                issues.append(f"Host {host.name} missing splunk_type")
            if not host.splunk_version:
                issues.append(f"Host {host.name} missing splunk_version")
        
        return issues
