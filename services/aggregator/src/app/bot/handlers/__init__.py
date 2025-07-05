from aiogram import Router  # type: ignore

from . import registration, subscription, general, premium


def setup_handlers() -> Router:
    """Setup all handlers and return main router"""
    main_router = Router()

    main_router.include_router(registration.router)
    main_router.include_router(subscription.router)
    main_router.include_router(premium.router)
    main_router.include_router(general.router)

    return main_router
