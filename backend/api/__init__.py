from .routes_health import router as health_router
from .routes_auth import router as auth_router
from .routes_chain import router as chain_router
from .routes_records import router as records_router
from .routes_ai import router as ai_router
from .routes_ai_gp import router as ai_gp_router
from .routes_ai_farmer import router as ai_farmer_router
from .routes_ai_warehouse import router as ai_warehouse_router
from .routes_warehouse_storage import router as warehouse_storage_router
from .routes_warehouse_dispatch import router as warehouse_dispatch_router

__all__ = [
    "health_router",
    "auth_router",
    "chain_router",
    "records_router",
    "ai_router",
    "ai_gp_router",
    "ai_farmer_router",
    "ai_warehouse_router",
    "warehouse_storage_router",
    "warehouse_dispatch_router",
]

