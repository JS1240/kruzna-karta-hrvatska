from app.routes.categories import router as categories_router
from app.routes.events import router as events_router
from app.routes.venues import router as venues_router

__all__ = [
    "categories_router",
    "events_router",
    "venues_router",
]
