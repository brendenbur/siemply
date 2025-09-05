#!/usr/bin/env python3
"""
Siemply Custom Script - Rotate SSH Keys
Rotates SSH keys for Splunk user on target hosts
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(cmd, timeout=300):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            'exit_code': 124,
            'stdout': '',
            'stderr': f'Command timed out after {timeout} seconds'
        }
    except Exception as e:
        return {
            'exit_code': 1,
            'stdout': '',
            'stderr': str(e)
        }


def backup_existing_keys(backup_dir):
    """Backup existing SSH keys"""
    logger.info("Backing up existing SSH keys...")
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup authorized_keys
    authorized_keys_path = Path.home() / '.ssh' / 'authorized_keys'
    if authorized_keys_path.exists():
        backup_path = Path(backup_dir) / f'authorized_keys_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        result = run_command(f'cp {authorized_keys_path} {backup_path}')
        if result['exit_code'] == 0:
            logger.info(f"Backed up authorized_keys to {backup_path}")
        else:
            logger.error(f"Failed to backup authorized_keys: {result['stderr']}")
            return False
    
    # Backup private key
    private_key_path = Path.home() / '.ssh' / 'id_rsa'
    if private_key_path.exists():
        backup_path = Path(backup_dir) / f'id_rsa_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        result = run_command(f'cp {private_key_path} {backup_path}')
        if result['exit_code'] == 0:
            logger.info(f"Backed up private key to {backup_path}")
        else:
            logger.error(f"Failed to backup private key: {result['stderr']}")
            return False
    
    return True


def generate_new_keypair(key_type='rsa', key_size=4096, comment='siemply-rotated'):
    """Generate new SSH key pair"""
    logger.info(f"Generating new {key_type} key pair...")
    
    # Remove existing keys
    private_key_path = Path.home() / '.ssh' / f'id_{key_type}'
    public_key_path = Path.home() / '.ssh' / f'id_{key_type}.pub'
    
    if private_key_path.exists():
        private_key_path.unlink()
    if public_key_path.exists():
        public_key_path.unlink()
    
    # Generate new key pair
    cmd = f'ssh-keygen -t {key_type} -b {key_size} -f {private_key_path} -N "" -C "{comment}"'
    result = run_command(cmd)
    
    if result['exit_code'] == 0:
        logger.info("New key pair generated successfully")
        return True
    else:
        logger.error(f"Failed to generate new key pair: {result['stderr']}")
        return False


def update_authorized_keys(public_key_path):
    """Update authorized_keys file with new public key"""
    logger.info("Updating authorized_keys file...")
    
    authorized_keys_path = Path.home() / '.ssh' / 'authorized_keys'
    
    # Read existing authorized_keys
    existing_keys = []
    if authorized_keys_path.exists():
        with open(authorized_keys_path, 'r') as f:
            existing_keys = f.readlines()
    
    # Read new public key
    with open(public_key_path, 'r') as f:
        new_key = f.read().strip()
    
    # Remove old keys with same comment
    comment = new_key.split()[-1] if len(new_key.split()) > 2 else ''
    filtered_keys = [key for key in existing_keys if not key.strip().endswith(comment)]
    
    # Add new key
    filtered_keys.append(new_key + '\n')
    
    # Write updated authorized_keys
    with open(authorized_keys_path, 'w') as f:
        f.writelines(filtered_keys)
    
    # Set proper permissions
    run_command(f'chmod 600 {authorized_keys_path}')
    run_command(f'chown {os.getenv("USER", "splunk")}:{os.getenv("USER", "splunk")} {authorized_keys_path}')
    
    logger.info("Authorized_keys file updated successfully")
    return True


def update_ssh_config():
    """Update SSH client configuration"""
    logger.info("Updating SSH client configuration...")
    
    ssh_config_path = Path.home() / '.ssh' / 'config'
    
    # Create SSH config if it doesn't exist
    if not ssh_config_path.exists():
        ssh_config_path.parent.mkdir(exist_ok=True)
        ssh_config_path.touch()
    
    # Read existing config
    config_lines = []
    if ssh_config_path.exists():
        with open(ssh_config_path, 'r') as f:
            config_lines = f.readlines()
    
    # Update or add IdentityFile directive
    updated = False
    for i, line in enumerate(config_lines):
        if line.strip().startswith('IdentityFile'):
            config_lines[i] = f'    IdentityFile ~/.ssh/id_rsa\n'
            updated = True
            break
    
    if not updated:
        # Add IdentityFile directive
        config_lines.append('    IdentityFile ~/.ssh/id_rsa\n')
    
    # Write updated config
    with open(ssh_config_path, 'w') as f:
        f.writelines(config_lines)
    
    # Set proper permissions
    run_command(f'chmod 600 {ssh_config_path}')
    
    logger.info("SSH client configuration updated successfully")
    return True


def restart_ssh_service():
    """Restart SSH service to apply changes"""
    logger.info("Restarting SSH service...")
    
    # Try different service management commands
    restart_commands = [
        'systemctl restart sshd',
        'systemctl restart ssh',
        'service sshd restart',
        'service ssh restart',
        '/etc/init.d/ssh restart'
    ]
    
    for cmd in restart_commands:
        result = run_command(cmd)
        if result['exit_code'] == 0:
            logger.info("SSH service restarted successfully")
            return True
        else:
            logger.debug(f"Command failed: {cmd} - {result['stderr']}")
    
    logger.warning("Could not restart SSH service - manual restart may be required")
    return False


def test_ssh_connectivity():
    """Test SSH connectivity with new keys"""
    logger.info("Testing SSH connectivity...")
    
    # Test localhost connection
    result = run_command('ssh -o StrictHostKeyChecking=no localhost "echo SSH test successful"')
    
    if result['exit_code'] == 0:
        logger.info("SSH connectivity test successful")
        return True
    else:
        logger.error(f"SSH connectivity test failed: {result['stderr']}")
        return False


def cleanup_old_keys(backup_dir, retention_days=30):
    """Clean up old backup keys"""
    logger.info(f"Cleaning up old backup keys (older than {retention_days} days)...")
    
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        return True
    
    # Find old backup files
    cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
    
    for file_path in backup_path.glob('*'):
        if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
            try:
                file_path.unlink()
                logger.info(f"Removed old backup: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to remove old backup {file_path}: {e}")
    
    return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Rotate SSH keys for Splunk user')
    parser.add_argument('--key-type', default='rsa', choices=['rsa', 'ed25519', 'ecdsa'],
                       help='SSH key type to generate')
    parser.add_argument('--key-size', type=int, default=4096,
                       help='SSH key size (for RSA keys)')
    parser.add_argument('--backup-dir', default='/opt/splunk/ssh_backups',
                       help='Directory to store key backups')
    parser.add_argument('--retention-days', type=int, default=30,
                       help='Number of days to retain backup keys')
    parser.add_argument('--restart-ssh', action='store_true',
                       help='Restart SSH service after key rotation')
    parser.add_argument('--test-connectivity', action='store_true',
                       help='Test SSH connectivity after key rotation')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    logger.info("Starting SSH key rotation...")
    logger.info(f"Key type: {args.key_type}")
    logger.info(f"Key size: {args.key_size}")
    logger.info(f"Backup directory: {args.backup_dir}")
    logger.info(f"Retention days: {args.retention_days}")
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        return 0
    
    try:
        # Step 1: Backup existing keys
        if not backup_existing_keys(args.backup_dir):
            logger.error("Failed to backup existing keys")
            return 1
        
        # Step 2: Generate new key pair
        if not generate_new_keypair(args.key_type, args.key_size):
            logger.error("Failed to generate new key pair")
            return 1
        
        # Step 3: Update authorized_keys
        public_key_path = Path.home() / '.ssh' / f'id_{args.key_type}.pub'
        if not update_authorized_keys(public_key_path):
            logger.error("Failed to update authorized_keys")
            return 1
        
        # Step 4: Update SSH config
        if not update_ssh_config():
            logger.error("Failed to update SSH config")
            return 1
        
        # Step 5: Restart SSH service (if requested)
        if args.restart_ssh:
            if not restart_ssh_service():
                logger.warning("SSH service restart failed - manual restart may be required")
        
        # Step 6: Test connectivity (if requested)
        if args.test_connectivity:
            if not test_ssh_connectivity():
                logger.error("SSH connectivity test failed")
                return 1
        
        # Step 7: Clean up old keys
        cleanup_old_keys(args.backup_dir, args.retention_days)
        
        logger.info("SSH key rotation completed successfully")
        
        # Output new public key for reference
        with open(public_key_path, 'r') as f:
            new_public_key = f.read().strip()
        
        print("\n" + "="*60)
        print("NEW PUBLIC KEY (for reference):")
        print("="*60)
        print(new_public_key)
        print("="*60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error during key rotation: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
