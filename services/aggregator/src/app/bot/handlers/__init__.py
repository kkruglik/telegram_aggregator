from aiogram import Router  # type: ignore

from . import debug, general, keywords, registration, subscription


def setup_handlers() -> Router:
    """Setup all handlers and return main router"""
    main_router = Router()

    main_router.include_router(registration.router)
    main_router.include_router(subscription.router)
    main_router.include_router(keywords.router)
    main_router.include_router(debug.router)
    main_router.include_router(general.router)

    return main_router
