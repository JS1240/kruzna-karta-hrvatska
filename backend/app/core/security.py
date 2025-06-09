"""
Database security hardening and GDPR compliance system.
"""

import os
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import re

from sqlalchemy import text, func
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from .database import get_db
from .config import settings

logger = logging.getLogger(__name__)


class DataCategory(Enum):
    """GDPR data categories for classification."""
    PERSONAL_IDENTIFIABLE = "personal_identifiable"
    SENSITIVE_PERSONAL = "sensitive_personal"
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    PUBLIC = "public"


class ProcessingLawfulBasis(Enum):
    """GDPR lawful basis for processing."""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class DataRetentionPeriod(Enum):
    """Data retention periods for different types."""
    USER_PROFILES = 1095  # 3 years
    EVENT_DATA = 2555  # 7 years (business records)
    ANALYTICS_DATA = 90  # 3 months
    AUDIT_LOGS = 2555  # 7 years (legal requirement)
    SESSION_DATA = 30  # 30 days
    TEMPORARY_DATA = 7  # 7 days


@dataclass
class DataProcessingRecord:
    """GDPR Article 30 processing record."""
    activity_name: str
    purpose: str
    data_categories: List[DataCategory]
    lawful_basis: ProcessingLawfulBasis
    data_subjects: str
    recipients: List[str]
    retention_period: int
    technical_measures: List[str]
    organizational_measures: List[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class PersonalDataInventory:
    """Inventory of personal data in the system."""
    table_name: str
    column_name: str
    data_category: DataCategory
    is_sensitive: bool
    encryption_required: bool
    retention_days: int
    anonymization_method: Optional[str]
    legal_basis: ProcessingLawfulBasis


@dataclass
class DataSubjectRequest:
    """GDPR data subject request tracking."""
    request_id: str
    request_type: str  # access, rectification, erasure, portability, restriction
    user_id: int
    email: str
    requested_at: datetime
    processed_at: Optional[datetime]
    status: str  # pending, processing, completed, rejected
    reason: Optional[str]
    processor_id: Optional[int]


class SecurityHardening:
    """Database security hardening implementation."""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Security configuration
        self.password_policy = {
            "min_length": 12,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_digits": True,
            "require_special": True,
            "max_age_days": 90,
            "history_count": 5
        }
        
        self.session_policy = {
            "max_session_duration": 3600,  # 1 hour
            "idle_timeout": 1800,  # 30 minutes
            "concurrent_sessions": 3,
            "require_2fa": False  # Can be enabled for admin users
        }
        
        logger.info("Security hardening service initialized")
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for data protection."""
        key_file = os.getenv("ENCRYPTION_KEY_FILE", "./encryption.key")
        
        try:
            # Try to load existing key
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    return f.read()
            
            # Generate new key
            password = os.getenv("ENCRYPTION_PASSWORD", "kruzna_karta_default_password").encode()
            salt = os.urandom(16)
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password))
            
            # Save key securely
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            
            # Set secure permissions
            os.chmod(key_file, 0o600)
            
            logger.info(f"Generated new encryption key: {key_file}")
            return key
        
        except Exception as e:
            logger.error(f"Failed to manage encryption key: {e}")
            # Fallback to environment-based key
            return Fernet.generate_key()
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data for storage."""
        if not data:
            return data
        
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data for use."""
        if not encrypted_data:
            return encrypted_data
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise
    
    def hash_personal_identifier(self, identifier: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash personal identifiers for pseudonymization."""
        if not salt:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for secure hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode('utf-8'),
            iterations=100000,
        )
        
        hash_bytes = kdf.derive(identifier.encode('utf-8'))
        hash_hex = hash_bytes.hex()
        
        return hash_hex, salt
    
    def validate_password_policy(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password against security policy."""
        errors = []
        
        if len(password) < self.password_policy["min_length"]:
            errors.append(f"Password must be at least {self.password_policy['min_length']} characters")
        
        if self.password_policy["require_uppercase"] and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.password_policy["require_lowercase"] and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.password_policy["require_digits"] and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if self.password_policy["require_special"] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    def audit_database_access(self, user_id: int, operation: str, table_name: str, 
                            record_id: Optional[int] = None, ip_address: Optional[str] = None):
        """Audit database access for compliance."""
        try:
            db = next(get_db())
            
            audit_record = {
                "user_id": user_id,
                "operation": operation,  # SELECT, INSERT, UPDATE, DELETE
                "table_name": table_name,
                "record_id": record_id,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow(),
                "session_id": self._get_current_session_id()
            }
            
            # Insert audit record
            db.execute(text("""
                INSERT INTO audit_logs (user_id, operation, table_name, record_id, 
                                      ip_address, timestamp, session_id)
                VALUES (:user_id, :operation, :table_name, :record_id, 
                        :ip_address, :timestamp, :session_id)
            """), audit_record)
            
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to audit database access: {e}")
    
    def _get_current_session_id(self) -> Optional[str]:
        """Get current session ID for audit trail."""
        # This would be implemented based on your session management
        # For now, return a placeholder
        return "session_placeholder"
    
    def check_data_access_permissions(self, user_id: int, table_name: str, 
                                    operation: str) -> Tuple[bool, Optional[str]]:
        """Check if user has permission to access specific data."""
        try:
            db = next(get_db())
            
            # Check user role and permissions
            result = db.execute(text("""
                SELECT r.name as role_name, p.permissions
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id
                JOIN roles r ON ur.role_id = r.id
                LEFT JOIN role_permissions rp ON r.id = rp.role_id
                LEFT JOIN permissions p ON rp.permission_id = p.id
                WHERE u.id = :user_id AND u.is_active = true
            """), {"user_id": user_id}).fetchall()
            
            if not result:
                return False, "User not found or inactive"
            
            # Check specific table permissions
            allowed_operations = []
            for row in result:
                if row.permissions:
                    perms = json.loads(row.permissions)
                    table_perms = perms.get(table_name, [])
                    allowed_operations.extend(table_perms)
            
            if operation.upper() in [op.upper() for op in allowed_operations]:
                return True, None
            
            return False, f"User does not have {operation} permission on {table_name}"
        
        except Exception as e:
            logger.error(f"Failed to check data access permissions: {e}")
            return False, f"Permission check failed: {str(e)}"
        finally:
            db.close()


class GDPRCompliance:
    """GDPR compliance implementation for Croatian events platform."""
    
    def __init__(self):
        self.security = SecurityHardening()
        
        # Personal data inventory for Croatian events platform
        self.data_inventory = [
            PersonalDataInventory(
                table_name="users",
                column_name="email",
                data_category=DataCategory.PERSONAL_IDENTIFIABLE,
                is_sensitive=False,
                encryption_required=True,
                retention_days=DataRetentionPeriod.USER_PROFILES.value,
                anonymization_method="pseudonymization",
                legal_basis=ProcessingLawfulBasis.CONTRACT
            ),
            PersonalDataInventory(
                table_name="users",
                column_name="phone_number",
                data_category=DataCategory.PERSONAL_IDENTIFIABLE,
                is_sensitive=False,
                encryption_required=True,
                retention_days=DataRetentionPeriod.USER_PROFILES.value,
                anonymization_method="masking",
                legal_basis=ProcessingLawfulBasis.CONTRACT
            ),
            PersonalDataInventory(
                table_name="users",
                column_name="date_of_birth",
                data_category=DataCategory.SENSITIVE_PERSONAL,
                is_sensitive=True,
                encryption_required=True,
                retention_days=DataRetentionPeriod.USER_PROFILES.value,
                anonymization_method="generalization",
                legal_basis=ProcessingLawfulBasis.CONSENT
            ),
            PersonalDataInventory(
                table_name="event_views",
                column_name="user_id",
                data_category=DataCategory.BEHAVIORAL,
                is_sensitive=False,
                encryption_required=False,
                retention_days=DataRetentionPeriod.ANALYTICS_DATA.value,
                anonymization_method="aggregation",
                legal_basis=ProcessingLawfulBasis.LEGITIMATE_INTERESTS
            ),
            PersonalDataInventory(
                table_name="user_interactions",
                column_name="ip_address",
                data_category=DataCategory.TECHNICAL,
                is_sensitive=False,
                encryption_required=True,
                retention_days=DataRetentionPeriod.ANALYTICS_DATA.value,
                anonymization_method="masking",
                legal_basis=ProcessingLawfulBasis.LEGITIMATE_INTERESTS
            )
        ]
        
        # Processing activities for Article 30 record
        self.processing_activities = [
            DataProcessingRecord(
                activity_name="Event Management Platform",
                purpose="Providing Croatian events information and booking services",
                data_categories=[
                    DataCategory.PERSONAL_IDENTIFIABLE,
                    DataCategory.BEHAVIORAL,
                    DataCategory.TECHNICAL
                ],
                lawful_basis=ProcessingLawfulBasis.CONTRACT,
                data_subjects="Croatian residents and tourists interested in events",
                recipients=["Event organizers", "Payment processors", "Analytics providers"],
                retention_period=DataRetentionPeriod.USER_PROFILES.value,
                technical_measures=[
                    "AES-256 encryption",
                    "TLS 1.3 for data in transit",
                    "Access controls and authentication",
                    "Database audit logging",
                    "Regular security updates"
                ],
                organizational_measures=[
                    "Staff training on GDPR compliance",
                    "Data protection impact assessments",
                    "Incident response procedures",
                    "Regular compliance audits",
                    "Privacy by design principles"
                ],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        logger.info("GDPR compliance service initialized")
    
    def process_data_subject_request(self, request: DataSubjectRequest) -> Dict[str, Any]:
        """Process GDPR data subject requests."""
        try:
            if request.request_type == "access":
                return self._handle_access_request(request)
            elif request.request_type == "rectification":
                return self._handle_rectification_request(request)
            elif request.request_type == "erasure":
                return self._handle_erasure_request(request)
            elif request.request_type == "portability":
                return self._handle_portability_request(request)
            elif request.request_type == "restriction":
                return self._handle_restriction_request(request)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown request type: {request.request_type}"
                }
        
        except Exception as e:
            logger.error(f"Failed to process data subject request: {e}")
            return {
                "status": "error",
                "message": f"Request processing failed: {str(e)}"
            }
    
    def _handle_access_request(self, request: DataSubjectRequest) -> Dict[str, Any]:
        """Handle GDPR Article 15 - Right of access."""
        try:
            db = next(get_db())
            
            # Collect all personal data for the user
            user_data = {}
            
            # User profile data
            user_result = db.execute(text("""
                SELECT id, email, first_name, last_name, phone_number, 
                       date_of_birth, created_at, last_login
                FROM users WHERE id = :user_id
            """), {"user_id": request.user_id}).fetchone()
            
            if user_result:
                user_data["profile"] = {
                    "id": user_result.id,
                    "email": self.security.decrypt_sensitive_data(user_result.email) if user_result.email else None,
                    "first_name": user_result.first_name,
                    "last_name": user_result.last_name,
                    "phone_number": self.security.decrypt_sensitive_data(user_result.phone_number) if user_result.phone_number else None,
                    "date_of_birth": user_result.date_of_birth.isoformat() if user_result.date_of_birth else None,
                    "created_at": user_result.created_at.isoformat(),
                    "last_login": user_result.last_login.isoformat() if user_result.last_login else None
                }
            
            # Event interactions
            interactions = db.execute(text("""
                SELECT event_id, interaction_type, interacted_at
                FROM user_interactions 
                WHERE user_id = :user_id
                ORDER BY interacted_at DESC
                LIMIT 1000
            """), {"user_id": request.user_id}).fetchall()
            
            user_data["event_interactions"] = [
                {
                    "event_id": interaction.event_id,
                    "type": interaction.interaction_type,
                    "timestamp": interaction.interacted_at.isoformat()
                }
                for interaction in interactions
            ]
            
            # Event views
            views = db.execute(text("""
                SELECT event_id, viewed_at
                FROM event_views 
                WHERE user_id = :user_id
                ORDER BY viewed_at DESC
                LIMIT 1000
            """), {"user_id": request.user_id}).fetchall()
            
            user_data["event_views"] = [
                {
                    "event_id": view.event_id,
                    "timestamp": view.viewed_at.isoformat()
                }
                for view in views
            ]
            
            # Processing information
            user_data["processing_info"] = {
                "purposes": ["Event discovery", "User experience improvement", "Analytics"],
                "legal_basis": "Contract performance and legitimate interests",
                "retention_period": f"{DataRetentionPeriod.USER_PROFILES.value} days",
                "data_sources": ["User registration", "Website interactions", "Event bookings"],
                "recipients": ["Event organizers", "Analytics processors"],
                "rights": [
                    "Right to rectification",
                    "Right to erasure",
                    "Right to restrict processing",
                    "Right to data portability",
                    "Right to object",
                    "Right to withdraw consent"
                ]
            }
            
            db.close()
            
            return {
                "status": "completed",
                "data": user_data,
                "request_id": request.request_id,
                "processed_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to handle access request: {e}")
            return {
                "status": "error",
                "message": f"Access request failed: {str(e)}"
            }
    
    def _handle_erasure_request(self, request: DataSubjectRequest) -> Dict[str, Any]:
        """Handle GDPR Article 17 - Right to erasure."""
        try:
            db = next(get_db())
            
            # Check if erasure is legally possible
            legal_check = self._check_erasure_legality(request.user_id, db)
            if not legal_check["can_erase"]:
                return {
                    "status": "rejected",
                    "reason": legal_check["reason"],
                    "request_id": request.request_id
                }
            
            # Perform erasure/anonymization
            erasure_actions = []
            
            # Anonymize user profile (keep for business purposes but remove personal data)
            db.execute(text("""
                UPDATE users 
                SET email = :anon_email,
                    first_name = 'Anonymous',
                    last_name = 'User',
                    phone_number = NULL,
                    date_of_birth = NULL,
                    is_active = false,
                    gdpr_erased = true,
                    erased_at = :erased_at
                WHERE id = :user_id
            """), {
                "anon_email": f"erased_user_{request.user_id}@anonymized.local",
                "erased_at": datetime.utcnow(),
                "user_id": request.user_id
            })
            erasure_actions.append("User profile anonymized")
            
            # Remove or anonymize behavioral data older than 30 days
            db.execute(text("""
                DELETE FROM user_interactions 
                WHERE user_id = :user_id 
                AND interacted_at < :cutoff_date
            """), {
                "user_id": request.user_id,
                "cutoff_date": datetime.utcnow() - timedelta(days=30)
            })
            erasure_actions.append("Old interaction data deleted")
            
            # Anonymize recent interactions (keep aggregated for analytics)
            db.execute(text("""
                UPDATE user_interactions 
                SET user_id = 0,
                    ip_address = '0.0.0.0'
                WHERE user_id = :user_id
            """), {"user_id": request.user_id})
            erasure_actions.append("Recent interactions anonymized")
            
            # Remove personal event views but keep aggregated counts
            db.execute(text("""
                DELETE FROM event_views 
                WHERE user_id = :user_id
            """), {"user_id": request.user_id})
            erasure_actions.append("Event view history deleted")
            
            # Log erasure action
            db.execute(text("""
                INSERT INTO gdpr_erasure_log (user_id, request_id, erased_at, actions)
                VALUES (:user_id, :request_id, :erased_at, :actions)
            """), {
                "user_id": request.user_id,
                "request_id": request.request_id,
                "erased_at": datetime.utcnow(),
                "actions": json.dumps(erasure_actions)
            })
            
            db.commit()
            db.close()
            
            return {
                "status": "completed",
                "actions": erasure_actions,
                "request_id": request.request_id,
                "processed_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to handle erasure request: {e}")
            return {
                "status": "error",
                "message": f"Erasure request failed: {str(e)}"
            }
    
    def _check_erasure_legality(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Check if data erasure is legally possible."""
        try:
            # Check for legal obligations to retain data
            active_bookings = db.execute(text("""
                SELECT COUNT(*) as count
                FROM event_bookings 
                WHERE user_id = :user_id 
                AND booking_date > :retention_cutoff
            """), {
                "user_id": user_id,
                "retention_cutoff": datetime.utcnow() - timedelta(days=2555)  # 7 years
            }).fetchone()
            
            if active_bookings and active_bookings.count > 0:
                return {
                    "can_erase": False,
                    "reason": "Legal obligation to retain booking records for 7 years"
                }
            
            # Check for ongoing legal proceedings
            legal_holds = db.execute(text("""
                SELECT COUNT(*) as count
                FROM legal_holds 
                WHERE user_id = :user_id 
                AND is_active = true
            """), {"user_id": user_id}).fetchone()
            
            if legal_holds and legal_holds.count > 0:
                return {
                    "can_erase": False,
                    "reason": "Data subject to legal hold"
                }
            
            return {"can_erase": True, "reason": None}
        
        except Exception as e:
            logger.error(f"Failed to check erasure legality: {e}")
            return {
                "can_erase": False,
                "reason": f"Legal check failed: {str(e)}"
            }
    
    def _handle_portability_request(self, request: DataSubjectRequest) -> Dict[str, Any]:
        """Handle GDPR Article 20 - Right to data portability."""
        try:
            # Get user data in structured format
            access_result = self._handle_access_request(request)
            
            if access_result["status"] != "completed":
                return access_result
            
            # Format data for portability (JSON format)
            portable_data = {
                "export_info": {
                    "platform": "Kruzna Karta Hrvatska",
                    "export_date": datetime.utcnow().isoformat(),
                    "format": "JSON",
                    "version": "1.0"
                },
                "user_data": access_result["data"]
            }
            
            return {
                "status": "completed",
                "data": portable_data,
                "format": "JSON",
                "request_id": request.request_id,
                "processed_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to handle portability request: {e}")
            return {
                "status": "error",
                "message": f"Portability request failed: {str(e)}"
            }
    
    def _handle_rectification_request(self, request: DataSubjectRequest) -> Dict[str, Any]:
        """Handle GDPR Article 16 - Right to rectification."""
        # This would require additional parameters for the corrections
        # For now, return a placeholder response
        return {
            "status": "pending",
            "message": "Rectification requests require manual review",
            "request_id": request.request_id
        }
    
    def _handle_restriction_request(self, request: DataSubjectRequest) -> Dict[str, Any]:
        """Handle GDPR Article 18 - Right to restriction of processing."""
        try:
            db = next(get_db())
            
            # Add processing restriction flag
            db.execute(text("""
                UPDATE users 
                SET processing_restricted = true,
                    restriction_date = :restriction_date
                WHERE id = :user_id
            """), {
                "restriction_date": datetime.utcnow(),
                "user_id": request.user_id
            })
            
            # Log restriction
            db.execute(text("""
                INSERT INTO gdpr_processing_restrictions (user_id, request_id, restricted_at)
                VALUES (:user_id, :request_id, :restricted_at)
            """), {
                "user_id": request.user_id,
                "request_id": request.request_id,
                "restricted_at": datetime.utcnow()
            })
            
            db.commit()
            db.close()
            
            return {
                "status": "completed",
                "message": "Processing restriction applied",
                "request_id": request.request_id,
                "processed_at": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to handle restriction request: {e}")
            return {
                "status": "error",
                "message": f"Restriction request failed: {str(e)}"
            }
    
    def run_data_retention_cleanup(self) -> Dict[str, Any]:
        """Run automated data retention cleanup based on GDPR requirements."""
        try:
            db = next(get_db())
            cleanup_actions = []
            
            # Clean up old analytics data (90 days retention)
            cutoff_analytics = datetime.utcnow() - timedelta(days=DataRetentionPeriod.ANALYTICS_DATA.value)
            
            result = db.execute(text("""
                DELETE FROM event_views 
                WHERE viewed_at < :cutoff_date
            """), {"cutoff_date": cutoff_analytics})
            cleanup_actions.append(f"Deleted {result.rowcount} old event views")
            
            result = db.execute(text("""
                DELETE FROM user_interactions 
                WHERE interacted_at < :cutoff_date
            """), {"cutoff_date": cutoff_analytics})
            cleanup_actions.append(f"Deleted {result.rowcount} old user interactions")
            
            # Clean up old session data (30 days retention)
            cutoff_sessions = datetime.utcnow() - timedelta(days=DataRetentionPeriod.SESSION_DATA.value)
            
            result = db.execute(text("""
                DELETE FROM user_sessions 
                WHERE created_at < :cutoff_date
            """), {"cutoff_date": cutoff_sessions})
            cleanup_actions.append(f"Deleted {result.rowcount} old user sessions")
            
            # Clean up temporary data (7 days retention)
            cutoff_temp = datetime.utcnow() - timedelta(days=DataRetentionPeriod.TEMPORARY_DATA.value)
            
            result = db.execute(text("""
                DELETE FROM search_logs 
                WHERE searched_at < :cutoff_date
            """), {"cutoff_date": cutoff_temp})
            cleanup_actions.append(f"Deleted {result.rowcount} old search logs")
            
            # Anonymize old audit logs (keep structure but remove personal data)
            cutoff_audit = datetime.utcnow() - timedelta(days=365)  # 1 year
            
            result = db.execute(text("""
                UPDATE audit_logs 
                SET ip_address = '0.0.0.0',
                    user_agent = 'anonymized'
                WHERE timestamp < :cutoff_date 
                AND ip_address != '0.0.0.0'
            """), {"cutoff_date": cutoff_audit})
            cleanup_actions.append(f"Anonymized {result.rowcount} old audit log entries")
            
            db.commit()
            db.close()
            
            logger.info(f"Data retention cleanup completed: {cleanup_actions}")
            
            return {
                "status": "completed",
                "actions": cleanup_actions,
                "cleanup_date": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Data retention cleanup failed: {e}")
            return {
                "status": "error",
                "message": f"Cleanup failed: {str(e)}"
            }
    
    def generate_privacy_report(self) -> Dict[str, Any]:
        """Generate privacy compliance report."""
        try:
            db = next(get_db())
            
            # Get data processing statistics
            stats = {}
            
            # Active users with personal data
            result = db.execute(text("""
                SELECT COUNT(*) as count
                FROM users 
                WHERE is_active = true AND gdpr_erased = false
            """)).fetchone()
            stats["active_users"] = result.count if result else 0
            
            # Users who requested erasure
            result = db.execute(text("""
                SELECT COUNT(*) as count
                FROM users 
                WHERE gdpr_erased = true
            """)).fetchone()
            stats["erased_users"] = result.count if result else 0
            
            # Recent data subject requests
            result = db.execute(text("""
                SELECT request_type, COUNT(*) as count
                FROM gdpr_requests 
                WHERE requested_at >= :since_date
                GROUP BY request_type
            """), {"since_date": datetime.utcnow() - timedelta(days=30)}).fetchall()
            
            stats["recent_requests"] = {row.request_type: row.count for row in result}
            
            # Data retention compliance
            retention_status = []
            
            for inventory_item in self.data_inventory:
                cutoff_date = datetime.utcnow() - timedelta(days=inventory_item.retention_days)
                
                result = db.execute(text(f"""
                    SELECT COUNT(*) as count
                    FROM {inventory_item.table_name}
                    WHERE created_at < :cutoff_date
                """), {"cutoff_date": cutoff_date}).fetchone()
                
                retention_status.append({
                    "table": inventory_item.table_name,
                    "column": inventory_item.column_name,
                    "retention_days": inventory_item.retention_days,
                    "expired_records": result.count if result else 0
                })
            
            db.close()
            
            return {
                "report_date": datetime.utcnow().isoformat(),
                "statistics": stats,
                "data_inventory": [
                    {
                        "table": item.table_name,
                        "column": item.column_name,
                        "category": item.data_category.value,
                        "sensitive": item.is_sensitive,
                        "encrypted": item.encryption_required,
                        "retention_days": item.retention_days,
                        "legal_basis": item.legal_basis.value
                    }
                    for item in self.data_inventory
                ],
                "retention_compliance": retention_status,
                "processing_activities": [
                    {
                        "name": activity.activity_name,
                        "purpose": activity.purpose,
                        "lawful_basis": activity.lawful_basis.value,
                        "retention_period": activity.retention_period
                    }
                    for activity in self.processing_activities
                ]
            }
        
        except Exception as e:
            logger.error(f"Failed to generate privacy report: {e}")
            return {
                "status": "error",
                "message": f"Report generation failed: {str(e)}"
            }


# Global instances
security_service = SecurityHardening()
gdpr_service = GDPRCompliance()


def get_security_service() -> SecurityHardening:
    """Get security service instance."""
    return security_service


def get_gdpr_service() -> GDPRCompliance:
    """Get GDPR compliance service instance."""
    return gdpr_service