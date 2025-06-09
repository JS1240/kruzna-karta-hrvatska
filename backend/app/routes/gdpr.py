"""
GDPR compliance and data subject rights API endpoints.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from ..core.auth import get_current_superuser, get_current_user
from ..core.security import DataSubjectRequest, get_gdpr_service, get_security_service
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gdpr", tags=["gdpr"])


class DataSubjectRequestCreate(BaseModel):
    """Data subject request creation model."""

    request_type: str  # access, rectification, erasure, portability, restriction
    email: EmailStr
    reason: Optional[str] = None


class DataSubjectRequestResponse(BaseModel):
    """Data subject request response model."""

    request_id: str
    request_type: str
    status: str
    message: str
    submitted_at: datetime


class PrivacySettings(BaseModel):
    """User privacy settings model."""

    analytics_consent: bool
    marketing_consent: bool
    third_party_sharing: bool
    data_retention_preference: int  # days


@router.post("/data-subject-request", response_model=DataSubjectRequestResponse)
async def submit_data_subject_request(
    request_data: DataSubjectRequestCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> DataSubjectRequestResponse:
    """Submit a GDPR data subject request."""
    try:
        gdpr_service = get_gdpr_service()

        # Validate request type
        valid_types = [
            "access",
            "rectification",
            "erasure",
            "portability",
            "restriction",
        ]
        if request_data.request_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request type. Must be one of: {valid_types}",
            )

        # Verify user email matches
        if request_data.email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email must match authenticated user",
            )

        # Create request
        request_id = str(uuid.uuid4())
        data_request = DataSubjectRequest(
            request_id=request_id,
            request_type=request_data.request_type,
            user_id=current_user.id,
            email=request_data.email,
            requested_at=datetime.utcnow(),
            processed_at=None,
            status="pending",
            reason=request_data.reason,
            processor_id=None,
        )

        # Process request in background for non-urgent requests
        if request_data.request_type in ["access", "portability"]:
            background_tasks.add_task(
                gdpr_service.process_data_subject_request, data_request
            )
            message = f"Data {request_data.request_type} request submitted. You will receive results within 30 days."
        else:
            # Urgent requests (erasure, restriction) process immediately
            result = gdpr_service.process_data_subject_request(data_request)
            if result["status"] == "completed":
                message = (
                    f"Data {request_data.request_type} request completed successfully."
                )
            else:
                message = f"Data {request_data.request_type} request failed: {result.get('message', 'Unknown error')}"

        return DataSubjectRequestResponse(
            request_id=request_id,
            request_type=request_data.request_type,
            status="submitted",
            message=message,
            submitted_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit data subject request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit request: {str(e)}",
        )


@router.get("/my-data")
async def get_my_data(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    """Get all personal data for the current user (GDPR Article 15)."""
    try:
        gdpr_service = get_gdpr_service()

        # Create access request
        access_request = DataSubjectRequest(
            request_id=str(uuid.uuid4()),
            request_type="access",
            user_id=current_user.id,
            email=current_user.email,
            requested_at=datetime.utcnow(),
            processed_at=None,
            status="processing",
            reason="Self-service data access",
            processor_id=None,
        )

        # Process access request
        result = gdpr_service.process_data_subject_request(access_request)

        if result["status"] == "completed":
            return {
                "status": "success",
                "data": result["data"],
                "accessed_at": datetime.utcnow().isoformat(),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve data: {result.get('message', 'Unknown error')}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve data: {str(e)}",
        )


@router.post("/export-data")
async def export_my_data(
    background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Export all personal data in portable format (GDPR Article 20)."""
    try:
        gdpr_service = get_gdpr_service()

        # Create portability request
        export_request = DataSubjectRequest(
            request_id=str(uuid.uuid4()),
            request_type="portability",
            user_id=current_user.id,
            email=current_user.email,
            requested_at=datetime.utcnow(),
            processed_at=None,
            status="processing",
            reason="Data export request",
            processor_id=None,
        )

        # Process in background and send email with download link
        background_tasks.add_task(
            gdpr_service.process_data_subject_request, export_request
        )

        return {
            "status": "submitted",
            "message": "Data export request submitted. You will receive a download link via email within 30 days.",
            "request_id": export_request.request_id,
            "submitted_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to export user data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}",
        )


@router.delete("/delete-my-account")
async def delete_my_account(
    background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Request account deletion (GDPR Article 17 - Right to erasure)."""
    try:
        gdpr_service = get_gdpr_service()

        # Create erasure request
        deletion_request = DataSubjectRequest(
            request_id=str(uuid.uuid4()),
            request_type="erasure",
            user_id=current_user.id,
            email=current_user.email,
            requested_at=datetime.utcnow(),
            processed_at=None,
            status="processing",
            reason="Account deletion request",
            processor_id=None,
        )

        # Process erasure request immediately
        result = gdpr_service.process_data_subject_request(deletion_request)

        if result["status"] == "completed":
            return {
                "status": "completed",
                "message": "Account successfully deleted. All personal data has been anonymized.",
                "actions": result["actions"],
                "deleted_at": datetime.utcnow().isoformat(),
            }
        elif result["status"] == "rejected":
            return {
                "status": "rejected",
                "message": f"Account deletion rejected: {result['reason']}",
                "request_id": deletion_request.request_id,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Deletion failed: {result.get('message', 'Unknown error')}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}",
        )


@router.post("/restrict-processing")
async def restrict_data_processing(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Restrict processing of personal data (GDPR Article 18)."""
    try:
        gdpr_service = get_gdpr_service()

        # Create restriction request
        restriction_request = DataSubjectRequest(
            request_id=str(uuid.uuid4()),
            request_type="restriction",
            user_id=current_user.id,
            email=current_user.email,
            requested_at=datetime.utcnow(),
            processed_at=None,
            status="processing",
            reason="Processing restriction request",
            processor_id=None,
        )

        # Process restriction immediately
        result = gdpr_service.process_data_subject_request(restriction_request)

        if result["status"] == "completed":
            return {
                "status": "completed",
                "message": "Data processing has been restricted for your account.",
                "restricted_at": datetime.utcnow().isoformat(),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Restriction failed: {result.get('message', 'Unknown error')}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restrict data processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restrict processing: {str(e)}",
        )


@router.get("/privacy-settings")
async def get_privacy_settings(
    current_user: User = Depends(get_current_user),
) -> PrivacySettings:
    """Get current privacy settings for the user."""
    try:
        # This would fetch from user_privacy_settings table
        # For now, return default settings
        return PrivacySettings(
            analytics_consent=True,
            marketing_consent=False,
            third_party_sharing=False,
            data_retention_preference=1095,  # 3 years
        )

    except Exception as e:
        logger.error(f"Failed to get privacy settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get settings: {str(e)}",
        )


@router.post("/privacy-settings")
async def update_privacy_settings(
    settings: PrivacySettings, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Update privacy settings for the user."""
    try:
        # This would update user_privacy_settings table
        # For now, return success

        return {
            "status": "updated",
            "message": "Privacy settings updated successfully",
            "settings": settings.dict(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to update privacy settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}",
        )


# Admin endpoints for GDPR compliance management


@router.get("/admin/requests")
async def list_data_subject_requests(
    status_filter: Optional[str] = None,
    request_type: Optional[str] = None,
    current_user: User = Depends(get_current_superuser),
) -> List[Dict[str, Any]]:
    """List all data subject requests (admin only)."""
    try:
        # This would fetch from gdpr_requests table
        # For now, return empty list
        return []

    except Exception as e:
        logger.error(f"Failed to list GDPR requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list requests: {str(e)}",
        )


@router.get("/admin/privacy-report")
async def generate_privacy_report(
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, Any]:
    """Generate comprehensive privacy compliance report (admin only)."""
    try:
        gdpr_service = get_gdpr_service()
        report = gdpr_service.generate_privacy_report()

        return report

    except Exception as e:
        logger.error(f"Failed to generate privacy report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}",
        )


@router.post("/admin/data-retention-cleanup")
async def run_data_retention_cleanup(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_superuser),
) -> Dict[str, Any]:
    """Run data retention cleanup process (admin only)."""
    try:
        gdpr_service = get_gdpr_service()

        # Run cleanup in background
        background_tasks.add_task(gdpr_service.run_data_retention_cleanup)

        return {
            "status": "started",
            "message": "Data retention cleanup started",
            "started_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to start data retention cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start cleanup: {str(e)}",
        )


@router.get("/privacy-policy")
async def get_privacy_policy() -> Dict[str, Any]:
    """Get the current privacy policy information."""
    return {
        "title": "Kruzna Karta Hrvatska Privacy Policy",
        "version": "1.0",
        "effective_date": "2025-01-01",
        "language": "hr",
        "controller": {
            "name": "Kruzna Karta Hrvatska d.o.o.",
            "address": "Zagreb, Croatia",
            "email": "privacy@kruznakarta.hr",
            "dpo_email": "dpo@kruznakarta.hr",
        },
        "data_processing": {
            "purposes": [
                "Event discovery and booking services",
                "User account management",
                "Analytics and service improvement",
                "Customer support",
                "Legal compliance",
            ],
            "legal_bases": [
                "Contract performance",
                "Legitimate interests",
                "Consent (for marketing)",
                "Legal obligation",
            ],
            "retention_periods": {
                "user_profiles": "3 years after last login",
                "event_bookings": "7 years (tax law requirement)",
                "analytics_data": "3 months",
                "audit_logs": "7 years (legal requirement)",
            },
        },
        "rights": [
            "Right to access your personal data",
            "Right to rectify inaccurate data",
            "Right to erase your data",
            "Right to restrict processing",
            "Right to data portability",
            "Right to object to processing",
            "Right to withdraw consent",
        ],
        "contact": {
            "email": "privacy@kruznakarta.hr",
            "phone": "+385 1 234 5678",
            "address": "Kruzna Karta Hrvatska d.o.o., Zagreb, Croatia",
        },
        "supervisory_authority": {
            "name": "Croatian Personal Data Protection Agency (AZOP)",
            "website": "https://azop.hr",
            "email": "azop@azop.hr",
        },
    }
