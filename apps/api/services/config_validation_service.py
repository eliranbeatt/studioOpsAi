"""
Configuration Validation Service
Validates environment configuration and provides secure credential management
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import warnings
from urllib.parse import urlparse
from pathlib import Path

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    # Try to load .env from current directory or project root
    env_path = Path.cwd() / '.env'
    if not env_path.exists():
        # Try parent directories
        for parent in Path.cwd().parents:
            env_path = parent / '.env'
            if env_path.exists():
                break
    
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # dotenv not available, skip loading
    pass

logger = logging.getLogger(__name__)

class ConfigSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ConfigValidationResult:
    key: str
    severity: ConfigSeverity
    message: str
    suggestion: Optional[str] = None
    current_value: Optional[str] = None

class ConfigValidator:
    """Validates environment configuration for StudioOps AI"""
    
    def __init__(self):
        self.validation_results: List[ConfigValidationResult] = []
        self.required_vars = self._get_required_variables()
        self.optional_vars = self._get_optional_variables()
        
    def _get_required_variables(self) -> Dict[str, Dict[str, Any]]:
        """Define required environment variables with validation rules"""
        return {
            # Database Configuration
            'DATABASE_URL': {
                'pattern': r'^postgresql://[^:]+:[^@]+@[^:]+:\d+/\w+',
                'description': 'PostgreSQL database connection URL',
                'example': 'postgresql://user:pass@host:5432/database'
            },
            
            # API Configuration
            'API_HOST': {
                'pattern': r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|localhost|0\.0\.0\.0)$',
                'description': 'API server host address',
                'example': '127.0.0.1 or 0.0.0.0'
            },
            'API_PORT': {
                'pattern': r'^\d{4,5}$',
                'description': 'API server port number',
                'example': '8000'
            }
        }
    
    def _get_optional_variables(self) -> Dict[str, Dict[str, Any]]:
        """Define optional environment variables with validation rules"""
        return {
            # External Services
            'OPENAI_API_KEY': {
                'pattern': r'^sk-[A-Za-z0-9]{32,}$',
                'description': 'OpenAI API key for AI services',
                'sensitive': True
            },
            'TRELLO_API_KEY': {
                'pattern': r'^[a-f0-9]{32}$',
                'description': 'Trello API key for board integration',
                'sensitive': True
            },
            'TRELLO_API_TOKEN': {
                'pattern': r'^[a-f0-9]{64}$',
                'description': 'Trello API token for authentication',
                'sensitive': True
            },
            
            # MinIO Configuration
            'MINIO_ENDPOINT': {
                'pattern': r'^[a-zA-Z0-9.-]+:\d+$',
                'description': 'MinIO server endpoint',
                'example': 'localhost:9000'
            },
            'MINIO_ACCESS_KEY': {
                'pattern': r'^[A-Za-z0-9]{3,}$',
                'description': 'MinIO access key',
                'sensitive': True
            },
            'MINIO_SECRET_KEY': {
                'pattern': r'^[A-Za-z0-9]{8,}$',
                'description': 'MinIO secret key',
                'sensitive': True
            },
            
            # Security
            'JWT_SECRET_KEY': {
                'pattern': r'^.{32,}$',
                'description': 'JWT secret key for authentication',
                'sensitive': True
            },
            
            # Logging
            'LOG_LEVEL': {
                'pattern': r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$',
                'description': 'Application log level',
                'example': 'INFO'
            },
            
            # Feature Flags
            'DEVELOPMENT_MODE': {
                'pattern': r'^(true|false)$',
                'description': 'Enable development mode features',
                'example': 'false'
            },
            'DEBUG_ENABLED': {
                'pattern': r'^(true|false)$',
                'description': 'Enable debug features',
                'example': 'false'
            }
        }
    
    def validate_all(self) -> List[ConfigValidationResult]:
        """Validate all configuration variables"""
        self.validation_results = []
        
        # Validate required variables
        for var_name, config in self.required_vars.items():
            self._validate_variable(var_name, config, required=True)
        
        # Validate optional variables
        for var_name, config in self.optional_vars.items():
            self._validate_variable(var_name, config, required=False)
        
        # Additional validation checks
        self._validate_database_connection()
        self._validate_security_settings()
        self._validate_service_configuration()
        
        return self.validation_results
    
    def _validate_variable(self, var_name: str, config: Dict[str, Any], required: bool = False):
        """Validate a single environment variable"""
        value = os.getenv(var_name)
        
        if value is None:
            if required:
                self.validation_results.append(ConfigValidationResult(
                    key=var_name,
                    severity=ConfigSeverity.ERROR,
                    message=f"Required environment variable '{var_name}' is not set",
                    suggestion=f"Set {var_name}={config.get('example', 'appropriate_value')}"
                ))
            else:
                self.validation_results.append(ConfigValidationResult(
                    key=var_name,
                    severity=ConfigSeverity.INFO,
                    message=f"Optional environment variable '{var_name}' is not set",
                    suggestion=f"Set {var_name} to enable {config.get('description', 'this feature')}"
                ))
            return
        
        # Validate pattern if specified
        if 'pattern' in config:
            if not re.match(config['pattern'], value):
                self.validation_results.append(ConfigValidationResult(
                    key=var_name,
                    severity=ConfigSeverity.ERROR,
                    message=f"Environment variable '{var_name}' has invalid format",
                    suggestion=f"Expected format: {config.get('example', config.get('description', 'valid format'))}",
                    current_value="***" if config.get('sensitive') else value[:20] + "..." if len(value) > 20 else value
                ))
                return
        
        # Additional validation for specific variables
        self._validate_specific_variable(var_name, value, config)
    
    def _validate_specific_variable(self, var_name: str, value: str, config: Dict[str, Any]):
        """Perform specific validation for certain variables"""
        
        if var_name == 'DATABASE_URL':
            self._validate_database_url(value)
        elif var_name == 'API_PORT':
            self._validate_port(var_name, value)
        elif var_name == 'MINIO_ENDPOINT':
            self._validate_endpoint(var_name, value)
        elif var_name == 'JWT_SECRET_KEY':
            self._validate_jwt_secret(value)
        elif var_name in ['OPENAI_API_KEY', 'TRELLO_API_KEY', 'TRELLO_API_TOKEN']:
            self._validate_api_key(var_name, value)
    
    def _validate_database_url(self, url: str):
        """Validate database URL format and accessibility"""
        try:
            parsed = urlparse(url)
            
            if parsed.scheme != 'postgresql':
                self.validation_results.append(ConfigValidationResult(
                    key='DATABASE_URL',
                    severity=ConfigSeverity.ERROR,
                    message="Database URL must use 'postgresql' scheme",
                    suggestion="Use format: postgresql://user:pass@host:port/database"
                ))
            
            if not parsed.username or not parsed.password:
                self.validation_results.append(ConfigValidationResult(
                    key='DATABASE_URL',
                    severity=ConfigSeverity.ERROR,
                    message="Database URL missing username or password",
                    suggestion="Include credentials: postgresql://user:pass@host:port/database"
                ))
            
            if not parsed.hostname or not parsed.port:
                self.validation_results.append(ConfigValidationResult(
                    key='DATABASE_URL',
                    severity=ConfigSeverity.ERROR,
                    message="Database URL missing hostname or port",
                    suggestion="Include host and port: postgresql://user:pass@host:port/database"
                ))
                
        except Exception as e:
            self.validation_results.append(ConfigValidationResult(
                key='DATABASE_URL',
                severity=ConfigSeverity.ERROR,
                message=f"Invalid database URL format: {e}",
                suggestion="Use format: postgresql://user:pass@host:port/database"
            ))
    
    def _validate_port(self, var_name: str, port_str: str):
        """Validate port number"""
        try:
            port = int(port_str)
            if port < 1024 or port > 65535:
                self.validation_results.append(ConfigValidationResult(
                    key=var_name,
                    severity=ConfigSeverity.WARNING,
                    message=f"Port {port} is outside recommended range",
                    suggestion="Use ports between 1024-65535 for better security"
                ))
        except ValueError:
            self.validation_results.append(ConfigValidationResult(
                key=var_name,
                severity=ConfigSeverity.ERROR,
                message=f"Invalid port number: {port_str}",
                suggestion="Port must be a number between 1024-65535"
            ))
    
    def _validate_endpoint(self, var_name: str, endpoint: str):
        """Validate service endpoint format"""
        if ':' not in endpoint:
            self.validation_results.append(ConfigValidationResult(
                key=var_name,
                severity=ConfigSeverity.ERROR,
                message=f"Invalid endpoint format: {endpoint}",
                suggestion="Use format: hostname:port (e.g., localhost:9000)"
            ))
    
    def _validate_jwt_secret(self, secret: str):
        """Validate JWT secret strength"""
        if len(secret) < 32:
            self.validation_results.append(ConfigValidationResult(
                key='JWT_SECRET_KEY',
                severity=ConfigSeverity.WARNING,
                message="JWT secret key is too short",
                suggestion="Use at least 32 characters for better security"
            ))
        
        if secret.lower() in ['secret', 'jwt_secret', 'dev_secret']:
            self.validation_results.append(ConfigValidationResult(
                key='JWT_SECRET_KEY',
                severity=ConfigSeverity.CRITICAL,
                message="JWT secret key is using a default/weak value",
                suggestion="Generate a strong random secret key"
            ))
    
    def _validate_api_key(self, var_name: str, key: str):
        """Validate API key format and strength"""
        if len(key) < 16:
            self.validation_results.append(ConfigValidationResult(
                key=var_name,
                severity=ConfigSeverity.WARNING,
                message=f"API key appears to be too short",
                suggestion="Verify the API key is complete and valid"
            ))
    
    def _validate_database_connection(self):
        """Validate database connection settings"""
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            return
        
        # Check for connection pool settings
        pool_size = os.getenv('DB_POOL_SIZE', '10')
        try:
            size = int(pool_size)
            if size < 5:
                self.validation_results.append(ConfigValidationResult(
                    key='DB_POOL_SIZE',
                    severity=ConfigSeverity.WARNING,
                    message="Database pool size is quite small",
                    suggestion="Consider increasing DB_POOL_SIZE for better performance"
                ))
            elif size > 50:
                self.validation_results.append(ConfigValidationResult(
                    key='DB_POOL_SIZE',
                    severity=ConfigSeverity.WARNING,
                    message="Database pool size is very large",
                    suggestion="Large pool sizes may impact memory usage"
                ))
        except ValueError:
            self.validation_results.append(ConfigValidationResult(
                key='DB_POOL_SIZE',
                severity=ConfigSeverity.ERROR,
                message="Invalid DB_POOL_SIZE value",
                suggestion="DB_POOL_SIZE must be a number"
            ))
    
    def _validate_security_settings(self):
        """Validate security-related configuration"""
        
        # Check production security settings
        development_mode = os.getenv('DEVELOPMENT_MODE', 'true').lower()
        debug_enabled = os.getenv('DEBUG_ENABLED', 'true').lower()
        
        if development_mode == 'false':  # Production mode
            if debug_enabled == 'true':
                self.validation_results.append(ConfigValidationResult(
                    key='DEBUG_ENABLED',
                    severity=ConfigSeverity.CRITICAL,
                    message="Debug mode is enabled in production",
                    suggestion="Set DEBUG_ENABLED=false in production for security"
                ))
            
            # Check for secure CORS settings
            cors_enabled = os.getenv('API_CORS_ENABLED', 'true').lower()
            if cors_enabled == 'true':
                self.validation_results.append(ConfigValidationResult(
                    key='API_CORS_ENABLED',
                    severity=ConfigSeverity.WARNING,
                    message="CORS is enabled in production",
                    suggestion="Consider disabling CORS and using a reverse proxy"
                ))
    
    def _validate_service_configuration(self):
        """Validate external service configuration"""
        
        # Check OpenAI configuration
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
            if model not in ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']:
                self.validation_results.append(ConfigValidationResult(
                    key='OPENAI_MODEL',
                    severity=ConfigSeverity.WARNING,
                    message=f"Unrecognized OpenAI model: {model}",
                    suggestion="Use a supported model like gpt-4 or gpt-3.5-turbo"
                ))
        
        # Check MinIO configuration consistency
        minio_endpoint = os.getenv('MINIO_ENDPOINT')
        minio_secure = os.getenv('MINIO_SECURE', 'false').lower()
        
        if minio_endpoint and 'localhost' in minio_endpoint and minio_secure == 'true':
            self.validation_results.append(ConfigValidationResult(
                key='MINIO_SECURE',
                severity=ConfigSeverity.WARNING,
                message="MinIO secure mode enabled for localhost",
                suggestion="Set MINIO_SECURE=false for local development"
            ))
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of validation results"""
        if not self.validation_results:
            self.validate_all()
        
        summary = {
            'total_checks': len(self.validation_results),
            'critical_issues': len([r for r in self.validation_results if r.severity == ConfigSeverity.CRITICAL]),
            'errors': len([r for r in self.validation_results if r.severity == ConfigSeverity.ERROR]),
            'warnings': len([r for r in self.validation_results if r.severity == ConfigSeverity.WARNING]),
            'info': len([r for r in self.validation_results if r.severity == ConfigSeverity.INFO]),
            'is_valid': len([r for r in self.validation_results if r.severity in [ConfigSeverity.CRITICAL, ConfigSeverity.ERROR]]) == 0
        }
        
        return summary
    
    def print_validation_report(self):
        """Print a formatted validation report"""
        if not self.validation_results:
            self.validate_all()
        
        summary = self.get_validation_summary()
        
        print("\n" + "="*60)
        print("STUDIOOPS AI CONFIGURATION VALIDATION REPORT")
        print("="*60)
        
        print(f"Total Checks: {summary['total_checks']}")
        print(f"Critical Issues: {summary['critical_issues']}")
        print(f"Errors: {summary['errors']}")
        print(f"Warnings: {summary['warnings']}")
        print(f"Info: {summary['info']}")
        print(f"Configuration Valid: {'✅ YES' if summary['is_valid'] else '❌ NO'}")
        
        if self.validation_results:
            print("\nDETAILS:")
            print("-"*60)
            
            for result in sorted(self.validation_results, key=lambda x: x.severity.value):
                icon = {
                    ConfigSeverity.CRITICAL: "🔴",
                    ConfigSeverity.ERROR: "❌",
                    ConfigSeverity.WARNING: "⚠️",
                    ConfigSeverity.INFO: "ℹ️"
                }[result.severity]
                
                print(f"{icon} {result.severity.value.upper()}: {result.key}")
                print(f"   {result.message}")
                if result.suggestion:
                    print(f"   💡 {result.suggestion}")
                if result.current_value:
                    print(f"   Current: {result.current_value}")
                print()
        
        print("="*60)

# Global instance
config_validator = ConfigValidator()

if __name__ == "__main__":
    # Run validation when script is executed directly
    config_validator.print_validation_report()