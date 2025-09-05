"""
Playbook YAML schema validation
"""
import yaml
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel, Field, field_validator


class PlaybookTask(BaseModel):
    type: str = Field(..., description="Task type: command, copy, template")
    name: str = Field(..., description="Task name")
    ignore_errors: bool = Field(False, description="Whether to ignore errors")
    timeout: Optional[int] = Field(None, description="Task timeout in seconds")
    
    # Command-specific fields
    cmd: Optional[str] = Field(None, description="Command to execute")
    
    # Copy/Template-specific fields
    src: Optional[str] = Field(None, description="Source file path")
    dest: Optional[str] = Field(None, description="Destination file path")
    mode: Optional[str] = Field(None, description="File permissions (octal)")
    
    # Template-specific fields
    vars: Optional[Dict[str, Any]] = Field(None, description="Template variables")
    
    @field_validator('type')
    @classmethod
    def validate_task_type(cls, v):
        allowed_types = ['command', 'copy', 'template']
        if v not in allowed_types:
            raise ValueError(f'Task type must be one of: {allowed_types}')
        return v
    
    @field_validator('cmd')
    @classmethod
    def validate_command_fields(cls, v, info):
        if info.data.get('type') == 'command' and not v:
            raise ValueError('Command tasks must have a cmd field')
        return v
    
    @field_validator('src', 'dest')
    @classmethod
    def validate_file_fields(cls, v, info):
        task_type = info.data.get('type')
        if task_type in ['copy', 'template'] and not v:
            raise ValueError(f'{task_type} tasks must have src and dest fields')
        return v


class PlaybookSchema(BaseModel):
    name: str = Field(..., description="Playbook name")
    description: Optional[str] = Field(None, description="Playbook description")
    tasks: List[PlaybookTask] = Field(..., description="List of tasks to execute")
    
    @field_validator('tasks')
    @classmethod
    def validate_tasks_not_empty(cls, v):
        if not v:
            raise ValueError('Playbook must have at least one task')
        return v


def validate_playbook_yaml(yaml_content: str) -> Tuple[bool, Optional[PlaybookSchema], Optional[str]]:
    """Validate playbook YAML content against schema"""
    try:
        # Parse YAML
        data = yaml.safe_load(yaml_content)
        if not data:
            return False, None, "Empty YAML content"
        
        # Validate against schema
        playbook = PlaybookSchema(**data)
        return True, playbook, None
        
    except yaml.YAMLError as e:
        return False, None, f"YAML parsing error: {str(e)}"
    except Exception as e:
        return False, None, f"Schema validation error: {str(e)}"


def load_playbook_from_yaml(yaml_content: str) -> Optional[PlaybookSchema]:
    """Load and validate playbook from YAML content"""
    is_valid, playbook, error = validate_playbook_yaml(yaml_content)
    if is_valid:
        return playbook
    else:
        raise ValueError(f"Invalid playbook: {error}")


# Sample playbooks
SAMPLE_PLAYBOOKS = {
    "package_update": {
        "name": "Package Update",
        "description": "Update packages and verify uptime",
        "tasks": [
            {
                "type": "command",
                "name": "Update packages",
                "cmd": "sudo apt-get update -y",
                "ignore_errors": False,
                "timeout": 120
            },
            {
                "type": "command",
                "name": "Show uptime",
                "cmd": "uptime"
            }
        ]
    },
    "splunk_health_check": {
        "name": "Splunk Health Check",
        "description": "Check Splunk service status and basic health",
        "tasks": [
            {
                "type": "command",
                "name": "Check Splunk status",
                "cmd": "sudo systemctl status splunk",
                "ignore_errors": True
            },
            {
                "type": "command",
                "name": "Check Splunk processes",
                "cmd": "ps aux | grep splunk | grep -v grep"
            },
            {
                "type": "command",
                "name": "Check disk space",
                "cmd": "df -h /opt/splunk"
            }
        ]
    },
    "deploy_config": {
        "name": "Deploy Configuration",
        "description": "Deploy configuration files to Splunk",
        "tasks": [
            {
                "type": "copy",
                "name": "Copy app configuration",
                "src": "./files/app.conf",
                "dest": "/opt/splunk/etc/apps/myapp/local/app.conf",
                "mode": "0644"
            },
            {
                "type": "template",
                "name": "Render server config",
                "src": "./templates/server.conf.j2",
                "dest": "/opt/splunk/etc/system/local/server.conf",
                "mode": "0644",
                "vars": {
                    "server_name": "splunk-server-01",
                    "cluster_master": "cm.example.com"
                }
            },
            {
                "type": "command",
                "name": "Restart Splunk",
                "cmd": "sudo /opt/splunk/bin/splunk restart",
                "timeout": 300
            }
        ]
    }
}
