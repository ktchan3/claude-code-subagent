"""
Security-specific configuration settings.

This module provides security configuration including authentication,
authorization, encryption, and security policies.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import timedelta
import secrets


class SecurityConfig(BaseModel):
    """
    Security configuration for authentication, encryption, and policies.
    
    Provides comprehensive security settings including JWT configuration,
    password policies, rate limiting, and security headers.
    """
    
    # JWT Configuration
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        min_length=32,
        description="Secret key for JWT signing and encryption"
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Access token expiration in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Refresh token expiration in days"
    )
    
    # Password Policy
    password_min_length: int = Field(
        default=8,
        ge=6,
        le=128,
        description="Minimum password length"
    )
    password_require_uppercase: bool = Field(
        default=True,
        description="Require uppercase letters in password"
    )
    password_require_lowercase: bool = Field(
        default=True,
        description="Require lowercase letters in password"
    )
    password_require_digits: bool = Field(
        default=True,
        description="Require digits in password"
    )
    password_require_special: bool = Field(
        default=True,
        description="Require special characters in password"
    )
    password_hash_rounds: int = Field(
        default=12,
        ge=4,
        le=20,
        description="Number of bcrypt hash rounds"
    )
    password_history_limit: int = Field(
        default=5,
        ge=0,
        le=24,
        description="Number of previous passwords to remember"
    )
    
    # Session Management
    session_timeout_minutes: int = Field(
        default=60,
        ge=5,
        le=480,
        description="Session timeout in minutes"
    )
    max_concurrent_sessions: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent sessions per user"
    )
    session_cleanup_interval_minutes: int = Field(
        default=15,
        ge=5,
        le=60,
        description="Session cleanup interval in minutes"
    )
    
    # Account Security
    max_login_attempts: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum failed login attempts before lockout"
    )
    lockout_duration_minutes: int = Field(
        default=15,
        ge=1,
        le=1440,
        description="Account lockout duration in minutes"
    )
    lockout_reset_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of attempts to reset before permanent lockout"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        le=10000,
        description="Rate limit per minute per client"
    )
    rate_limit_burst: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Rate limit burst capacity"
    )
    rate_limit_login_per_minute: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Login attempt rate limit per minute"
    )
    
    # API Key Security
    api_key_length: int = Field(
        default=32,
        ge=16,
        le=64,
        description="API key length in bytes"
    )
    api_key_expiry_days: Optional[int] = Field(
        default=365,
        ge=1,
        le=3650,
        description="API key expiration in days (None for no expiry)"
    )
    api_key_rate_limit_multiplier: float = Field(
        default=2.0,
        ge=0.1,
        le=10.0,
        description="Rate limit multiplier for API key users"
    )
    
    # Encryption Settings
    encryption_key_rotation_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Encryption key rotation interval in days"
    )
    data_encryption_enabled: bool = Field(
        default=True,
        description="Enable encryption for sensitive data at rest"
    )
    
    # Security Headers
    security_headers: Dict[str, str] = Field(
        default_factory=lambda: {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()"
        },
        description="HTTP security headers"
    )
    
    # HTTPS Settings
    force_https: bool = Field(
        default=False,
        description="Force HTTPS for all connections"
    )
    hsts_max_age: int = Field(
        default=31536000,
        ge=300,
        le=63072000,
        description="HSTS max age in seconds (1 year default)"
    )
    hsts_include_subdomains: bool = Field(
        default=True,
        description="Include subdomains in HSTS policy"
    )
    
    # Input Validation
    max_request_size: int = Field(
        default=10 * 1024 * 1024,
        ge=1024,
        le=100 * 1024 * 1024,
        description="Maximum request size in bytes"
    )
    max_json_depth: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum JSON nesting depth"
    )
    allowed_origins: List[str] = Field(
        default_factory=list,
        description="Allowed CORS origins"
    )
    
    # Audit Logging
    audit_log_enabled: bool = Field(
        default=True,
        description="Enable security audit logging"
    )
    audit_log_retention_days: int = Field(
        default=90,
        ge=1,
        le=2555,
        description="Audit log retention in days"
    )
    audit_log_sensitive_data: bool = Field(
        default=False,
        description="Include sensitive data in audit logs"
    )
    
    # Security Monitoring
    suspicious_activity_threshold: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Threshold for suspicious activity alerts"
    )
    security_alert_email: Optional[str] = Field(
        default=None,
        description="Email address for security alerts"
    )
    
    @field_validator("algorithm")
    @classmethod
    def validate_jwt_algorithm(cls, v):
        """Validate JWT algorithm."""
        allowed_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
        if v not in allowed_algorithms:
            raise ValueError(f"JWT algorithm must be one of: {allowed_algorithms}")
        return v
    
    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v):
        """Validate secret key strength."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        
        # Check for common weak keys
        weak_keys = [
            "your-secret-key-change-in-production",
            "dev-secret-key-not-for-production",
            "secret",
            "password",
            "123456789012345678901234567890123456"
        ]
        if v in weak_keys:
            raise ValueError("Secret key appears to be a default or weak value")
        
        return v
    
    def get_password_policy(self) -> Dict[str, Any]:
        """
        Get password policy configuration.
        
        Returns:
            Dictionary with password policy settings
        """
        return {
            "min_length": self.password_min_length,
            "require_uppercase": self.password_require_uppercase,
            "require_lowercase": self.password_require_lowercase,
            "require_digits": self.password_require_digits,
            "require_special": self.password_require_special,
            "hash_rounds": self.password_hash_rounds,
            "history_limit": self.password_history_limit,
        }
    
    def get_rate_limit_config(self) -> Dict[str, Any]:
        """
        Get rate limiting configuration.
        
        Returns:
            Dictionary with rate limiting settings
        """
        return {
            "per_minute": self.rate_limit_per_minute,
            "burst": self.rate_limit_burst,
            "login_per_minute": self.rate_limit_login_per_minute,
            "api_key_multiplier": self.api_key_rate_limit_multiplier,
        }
    
    def get_security_headers(self) -> Dict[str, str]:
        """
        Get security headers configuration.
        
        Returns:
            Dictionary with security headers
        """
        headers = dict(self.security_headers)
        
        # Add HSTS header if HTTPS is forced
        if self.force_https:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            headers["Strict-Transport-Security"] = hsts_value
        
        return headers
    
    def get_jwt_config(self) -> Dict[str, Any]:
        """
        Get JWT configuration.
        
        Returns:
            Dictionary with JWT settings
        """
        return {
            "secret_key": self.secret_key,
            "algorithm": self.algorithm,
            "access_token_expire": timedelta(minutes=self.access_token_expire_minutes),
            "refresh_token_expire": timedelta(days=self.refresh_token_expire_days),
        }
    
    def validate_password(self, password: str) -> tuple[bool, List[str]]:
        """
        Validate password against policy.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if len(password) < self.password_min_length:
            errors.append(f"Password must be at least {self.password_min_length} characters long")
        
        if self.password_require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.password_require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.password_require_digits and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if self.password_require_special:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                errors.append(f"Password must contain at least one special character ({special_chars})")
        
        return len(errors) == 0, errors