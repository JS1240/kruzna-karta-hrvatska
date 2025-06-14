from .analytics import router as analytics_router
from .auth import router as auth_router
from .backup import router as backup_router
from .booking import router as booking_router
from .categories import router as categories_router
from .croatian import router as croatian_router
from .events import router as events_router
from .gdpr import router as gdpr_router
from .monitoring import router as monitoring_router
from .performance import router as performance_router
from .recurring_events import router as recurring_events_router
from .scraping import router as scraping_router
from .social import router as social_router
from .system_test import router as system_test_router
from .recommendations import router as recommendations_router
from .third_party import router as third_party_router
from .translations import router as translations_router
from .user_events import router as user_events_router
from .users import router as users_router
from .venue_management import router as venue_management_router
from .venues import router as venues_router

__all__ = [
    "events_router",
    "categories_router",
    "venues_router",
    "auth_router",
    "users_router",
    "translations_router",
    "scraping_router",
    "analytics_router",
    "performance_router",
    "backup_router",
    "monitoring_router",
    "gdpr_router",
    "croatian_router",
    "booking_router",
    "recurring_events_router",
    "venue_management_router",
    "social_router",
    "user_events_router",
    "system_test_router",
    "recommendations_router",
    "third_party_router",
]
