from .register import r as register_router
from .admin import r as admin_router
from .dev import r as dev_router
from .channels import r as channels_router
from loader import dp

dp.include_router(register_router)
dp.include_router(dev_router)
dp.include_router(admin_router)
dp.include_router(channels_router)