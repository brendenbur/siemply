"""
Siemply Secrets Manager - Pluggable secrets backend
"""

import logging
import os
import json
import base64
from typing import Dict, Any, Optional, Union
from abc import ABC, abstractmethod
import yaml


class SecretsBackend(ABC):
    """Abstract base class for secrets backends"""
    
    @abstractmethod
    async def get_secret(self, key: str) -> Optional[str]:
        """Get a secret by key"""
        pass
    
    @abstractmethod
    async def set_secret(self, key: str, value: str) -> bool:
        """Set a secret by key"""
        pass
    
    @abstractmethod
    async def delete_secret(self, key: str) -> bool:
        """Delete a secret by key"""
        pass
    
    @abstractmethod
    async def list_secrets(self) -> list:
        """List all secret keys"""
        pass


class EnvironmentSecretsBackend(SecretsBackend):
    """Secrets backend using environment variables"""
    
    def __init__(self, prefix: str = "SIEMPLY_"):
        self.prefix = prefix
        self.logger = logging.getLogger(__name__)
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from environment variable"""
        env_key = f"{self.prefix}{key.upper()}"
        value = os.environ.get(env_key)
        if value:
            self.logger.debug(f"Retrieved secret from environment: {key}")
        return value
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Set secret in environment variable"""
        env_key = f"{self.prefix}{key.upper()}"
        os.environ[env_key] = value
        self.logger.debug(f"Set secret in environment: {key}")
        return True
    
    async def delete_secret(self, key: str) -> bool:
        """Delete secret from environment"""
        env_key = f"{self.prefix}{key.upper()}"
        if env_key in os.environ:
            del os.environ[env_key]
            self.logger.debug(f"Deleted secret from environment: {key}")
            return True
        return False
    
    async def list_secrets(self) -> list:
        """List all environment secrets"""
        secrets = []
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                secret_key = key[len(self.prefix):].lower()
                secrets.append(secret_key)
        return secrets


class FileSecretsBackend(SecretsBackend):
    """Secrets backend using encrypted file storage"""
    
    def __init__(self, secrets_file: str = "config/secrets.json", key_file: str = "config/secrets.key"):
        self.secrets_file = secrets_file
        self.key_file = key_file
        self.logger = logging.getLogger(__name__)
        self._secrets = {}
        self._encryption_key = None
    
    async def _load_encryption_key(self):
        """Load or generate encryption key"""
        if self._encryption_key:
            return
        
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                self._encryption_key = f.read()
        else:
            # Generate new key
            import secrets
            self._encryption_key = secrets.token_bytes(32)
            
            # Save key
            os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
            with open(self.key_file, 'wb') as f:
                f.write(self._encryption_key)
            
            self.logger.info(f"Generated new encryption key: {self.key_file}")
    
    async def _encrypt_value(self, value: str) -> str:
        """Encrypt a value"""
        await self._load_encryption_key()
        
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
        # Derive key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'siemply_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._encryption_key))
        
        # Encrypt value
        fernet = Fernet(key)
        encrypted_value = fernet.encrypt(value.encode())
        
        return base64.b64encode(encrypted_value).decode()
    
    async def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a value"""
        await self._load_encryption_key()
        
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
        # Derive key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'siemply_salt',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self._encryption_key))
        
        # Decrypt value
        fernet = Fernet(key)
        encrypted_bytes = base64.b64decode(encrypted_value)
        decrypted_value = fernet.decrypt(encrypted_bytes)
        
        return decrypted_value.decode()
    
    async def _load_secrets(self):
        """Load secrets from file"""
        if self._secrets:
            return
        
        if os.path.exists(self.secrets_file):
            try:
                with open(self.secrets_file, 'r') as f:
                    encrypted_secrets = json.load(f)
                
                # Decrypt secrets
                for key, encrypted_value in encrypted_secrets.items():
                    try:
                        decrypted_value = await self._decrypt_value(encrypted_value)
                        self._secrets[key] = decrypted_value
                    except Exception as e:
                        self.logger.warning(f"Failed to decrypt secret {key}: {e}")
                
                self.logger.info(f"Loaded {len(self._secrets)} secrets from file")
                
            except Exception as e:
                self.logger.error(f"Failed to load secrets file: {e}")
                self._secrets = {}
        else:
            self._secrets = {}
    
    async def _save_secrets(self):
        """Save secrets to file"""
        try:
            # Encrypt secrets
            encrypted_secrets = {}
            for key, value in self._secrets.items():
                encrypted_value = await self._encrypt_value(value)
                encrypted_secrets[key] = encrypted_value
            
            # Save to file
            os.makedirs(os.path.dirname(self.secrets_file), exist_ok=True)
            with open(self.secrets_file, 'w') as f:
                json.dump(encrypted_secrets, f, indent=2)
            
            self.logger.debug(f"Saved {len(self._secrets)} secrets to file")
            
        except Exception as e:
            self.logger.error(f"Failed to save secrets file: {e}")
            raise
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from file"""
        await self._load_secrets()
        value = self._secrets.get(key)
        if value:
            self.logger.debug(f"Retrieved secret from file: {key}")
        return value
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Set secret in file"""
        await self._load_secrets()
        self._secrets[key] = value
        await self._save_secrets()
        self.logger.debug(f"Set secret in file: {key}")
        return True
    
    async def delete_secret(self, key: str) -> bool:
        """Delete secret from file"""
        await self._load_secrets()
        if key in self._secrets:
            del self._secrets[key]
            await self._save_secrets()
            self.logger.debug(f"Deleted secret from file: {key}")
            return True
        return False
    
    async def list_secrets(self) -> list:
        """List all secrets"""
        await self._load_secrets()
        return list(self._secrets.keys())


class VaultSecretsBackend(SecretsBackend):
    """Secrets backend using HashiCorp Vault"""
    
    def __init__(self, vault_url: str, vault_token: str, vault_path: str = "secret/siemply"):
        self.vault_url = vault_url
        self.vault_token = vault_token
        self.vault_path = vault_path
        self.logger = logging.getLogger(__name__)
        self._client = None
    
    async def _get_client(self):
        """Get Vault client"""
        if self._client:
            return self._client
        
        try:
            import hvac
            
            self._client = hvac.Client(
                url=self.vault_url,
                token=self.vault_token
            )
            
            # Test connection
            if not self._client.is_authenticated():
                raise Exception("Vault authentication failed")
            
            self.logger.info("Connected to Vault")
            return self._client
            
        except ImportError:
            raise Exception("hvac library not installed. Install with: pip install hvac")
        except Exception as e:
            self.logger.error(f"Failed to connect to Vault: {e}")
            raise
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from Vault"""
        try:
            client = await self._get_client()
            
            # Read secret from Vault
            secret_path = f"{self.vault_path}/{key}"
            response = client.secrets.kv.v2.read_secret_version(path=secret_path)
            
            if response and 'data' in response:
                value = response['data']['data'].get('value')
                if value:
                    self.logger.debug(f"Retrieved secret from Vault: {key}")
                return value
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get secret from Vault: {e}")
            return None
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Set secret in Vault"""
        try:
            client = await self._get_client()
            
            # Write secret to Vault
            secret_path = f"{self.vault_path}/{key}"
            client.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                secret={'value': value}
            )
            
            self.logger.debug(f"Set secret in Vault: {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set secret in Vault: {e}")
            return False
    
    async def delete_secret(self, key: str) -> bool:
        """Delete secret from Vault"""
        try:
            client = await self._get_client()
            
            # Delete secret from Vault
            secret_path = f"{self.vault_path}/{key}"
            client.secrets.kv.v2.delete_metadata_and_all_versions(path=secret_path)
            
            self.logger.debug(f"Deleted secret from Vault: {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete secret from Vault: {e}")
            return False
    
    async def list_secrets(self) -> list:
        """List all secrets in Vault"""
        try:
            client = await self._get_client()
            
            # List secrets
            response = client.secrets.kv.v2.list_secrets(path=self.vault_path)
            
            if response and 'data' in response:
                return response['data']['keys']
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to list secrets from Vault: {e}")
            return []


class SecretsManager:
    """
    Centralized secrets management with pluggable backends
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.logger = logging.getLogger(__name__)
        
        # Available backends
        self.backends = {
            'env': EnvironmentSecretsBackend(),
            'file': FileSecretsBackend(),
            'vault': None  # Will be initialized if configured
        }
        
        # Default backend
        self.default_backend = 'env'
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Load secrets configuration"""
        config_file = os.path.join(self.config_dir, "secrets.yml")
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Set default backend
                self.default_backend = config.get('default_backend', 'env')
                
                # Configure Vault backend if specified
                vault_config = config.get('vault', {})
                if vault_config.get('enabled', False):
                    self.backends['vault'] = VaultSecretsBackend(
                        vault_url=vault_config.get('url'),
                        vault_token=vault_config.get('token'),
                        vault_path=vault_config.get('path', 'secret/siemply')
                    )
                
                # Configure file backend
                file_config = config.get('file', {})
                if file_config.get('enabled', True):
                    self.backends['file'] = FileSecretsBackend(
                        secrets_file=file_config.get('secrets_file', 'config/secrets.json'),
                        key_file=file_config.get('key_file', 'config/secrets.key')
                    )
                
                self.logger.info(f"Secrets configuration loaded, default backend: {self.default_backend}")
                
            except Exception as e:
                self.logger.warning(f"Failed to load secrets configuration: {e}")
    
    async def load(self):
        """Initialize secrets manager"""
        # Test default backend
        try:
            await self.backends[self.default_backend].list_secrets()
            self.logger.info(f"Secrets manager initialized with backend: {self.default_backend}")
        except Exception as e:
            self.logger.error(f"Failed to initialize secrets manager: {e}")
            raise
    
    async def get_secret(self, key: str, backend: Optional[str] = None) -> Optional[str]:
        """Get a secret by key"""
        backend_name = backend or self.default_backend
        
        if backend_name not in self.backends:
            self.logger.error(f"Unknown secrets backend: {backend_name}")
            return None
        
        backend_instance = self.backends[backend_name]
        if not backend_instance:
            self.logger.error(f"Secrets backend not configured: {backend_name}")
            return None
        
        try:
            return await backend_instance.get_secret(key)
        except Exception as e:
            self.logger.error(f"Failed to get secret {key} from {backend_name}: {e}")
            return None
    
    async def set_secret(self, key: str, value: str, backend: Optional[str] = None) -> bool:
        """Set a secret by key"""
        backend_name = backend or self.default_backend
        
        if backend_name not in self.backends:
            self.logger.error(f"Unknown secrets backend: {backend_name}")
            return False
        
        backend_instance = self.backends[backend_name]
        if not backend_instance:
            self.logger.error(f"Secrets backend not configured: {backend_name}")
            return False
        
        try:
            return await backend_instance.set_secret(key, value)
        except Exception as e:
            self.logger.error(f"Failed to set secret {key} in {backend_name}: {e}")
            return False
    
    async def delete_secret(self, key: str, backend: Optional[str] = None) -> bool:
        """Delete a secret by key"""
        backend_name = backend or self.default_backend
        
        if backend_name not in self.backends:
            self.logger.error(f"Unknown secrets backend: {backend_name}")
            return False
        
        backend_instance = self.backends[backend_name]
        if not backend_instance:
            self.logger.error(f"Secrets backend not configured: {backend_name}")
            return False
        
        try:
            return await backend_instance.delete_secret(key)
        except Exception as e:
            self.logger.error(f"Failed to delete secret {key} from {backend_name}: {e}")
            return False
    
    async def list_secrets(self, backend: Optional[str] = None) -> list:
        """List all secrets"""
        backend_name = backend or self.default_backend
        
        if backend_name not in self.backends:
            self.logger.error(f"Unknown secrets backend: {backend_name}")
            return []
        
        backend_instance = self.backends[backend_name]
        if not backend_instance:
            self.logger.error(f"Secrets backend not configured: {backend_name}")
            return []
        
        try:
            return await backend_instance.list_secrets()
        except Exception as e:
            self.logger.error(f"Failed to list secrets from {backend_name}: {e}")
            return []
    
    async def get_ssh_key_passphrase(self, key_file: str) -> Optional[str]:
        """Get SSH key passphrase for a key file"""
        key_name = os.path.basename(key_file)
        return await self.get_secret(f"ssh_key_passphrase_{key_name}")
    
    async def get_database_password(self, database: str) -> Optional[str]:
        """Get database password"""
        return await self.get_secret(f"database_password_{database}")
    
    async def get_api_token(self, service: str) -> Optional[str]:
        """Get API token for a service"""
        return await self.get_secret(f"api_token_{service}")
    
    async def get_webhook_url(self, webhook_name: str) -> Optional[str]:
        """Get webhook URL"""
        return await self.get_secret(f"webhook_url_{webhook_name}")
    
    def get_available_backends(self) -> list:
        """Get list of available backends"""
        return [name for name, backend in self.backends.items() if backend is not None]
    
    async def test_backend(self, backend_name: str) -> bool:
        """Test if a backend is working"""
        if backend_name not in self.backends:
            return False
        
        backend_instance = self.backends[backend_name]
        if not backend_instance:
            return False
        
        try:
            await backend_instance.list_secrets()
            return True
        except Exception:
            return False
