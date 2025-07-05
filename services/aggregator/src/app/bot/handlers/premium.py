import logging
from datetime import datetime

from aiogram import Router, F  # type: ignore
from aiogram.filters import Command  # type: ignore
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, SuccessfulPayment  # type: ignore

from ...core.registry import UserRegistry

logger = logging.getLogger("news_aggregator")

router = Router(name='premium')

PREMIUM_PRICE_STARS = 2
PREMIUM_DURATION_DAYS = 30


@router.message(Command("upgrade_premium"))
async def cmd_upgrade_premium(message: Message):
    """Handle /upgrade_premium command - start the upgrade premium process"""
    user_id = message.from_user.id
    user = await UserRegistry.get_or_create_user(user_id)
    if user.is_premium:
        logger.info(f"User {user_id} already has a premium")
        await message.answer("You already have premium subscription.")
        return

    prices = [LabeledPrice(label="XTR", amount=PREMIUM_PRICE_STARS)]

    timestamp = int(datetime.now().timestamp())
    payload = f"premium_{user_id}_{timestamp}"

    await message.answer_invoice(
        title="Evening Telegram Premium",
        description="Get unlimited amount of aggregated channels to your daily digest!",
        prices=prices,
        provider_token="",
        payload=payload,
        currency="XTR",
    )


@router.pre_checkout_query()
async def checkout_premium(pre_checkout_query: PreCheckoutQuery):
    try:
        if not pre_checkout_query.invoice_payload.startswith(f"premium_{pre_checkout_query.from_user.id}_"):
            logger.warning(f"Invalid payload format: {pre_checkout_query.invoice_payload}")
            await pre_checkout_query.answer(ok=False, error_message="Invalid request")
            return

        if pre_checkout_query.total_amount != PREMIUM_PRICE_STARS:
            logger.warning(f"Amount mismatch: expected {PREMIUM_PRICE_STARS}, got {pre_checkout_query.total_amount}")
            await pre_checkout_query.answer(
                ok=False,
                error_message="Invalid payment amount."
            )
            return

        if pre_checkout_query.currency != "XTR":
            logger.warning(f"Currency mismatch: expected XTR, got {pre_checkout_query.currency}")
            await pre_checkout_query.answer(
                ok=False,
                error_message="Invalid currency."
            )
            return

        user = await UserRegistry.get_or_create_user(pre_checkout_query.from_user.id)

        if user.is_premium:
            logger.warning(f"User {user.id} already has premium subscription.")
            await pre_checkout_query.answer(
                ok=False,
                error_message="You already have an active premium subscription."
            )
            return

        logger.info(
            f"Valid payment attempt: User {pre_checkout_query.from_user.id}, "
            f"Amount {pre_checkout_query.total_amount}"
        )

        await pre_checkout_query.answer(ok=True)

    except Exception as e:
        logger.error(f"Pre-checkout error: {e}")
        await pre_checkout_query.answer(ok=False, error_message="Payment failed")


@router.message(F.successful_payment)
async def on_successful_payment(message: Message):
    logger.info(f"Successful payment: {message}")
    try:
        user_id = message.from_user.id
        payment = message.successful_payment
        charge_id = payment.telegram_payment_charge_id
        user = await UserRegistry.get_or_create_user(user_id)

        logger.info(f"Processing payment: User {user_id}, Charge {charge_id}, Amount {payment.total_amount}")

        if not payment.invoice_payload.startswith(f"premium_{user_id}_"):
            logger.error(f"Invalid payload: {payment.invoice_payload} for user {user_id}")
            await message.answer("❌ Payment validation failed. Contact support.")
            return

        # TODO validate logic if user have a premium already and passed previous checks
        if user.is_premium:
            logger.warning(f"User {user.id} already has premium subscription.")
            await message.answer(
                f"✅ Payment received! You already have premium access.\n"
                f"💰 Payment: {payment.total_amount} ⭐\n"
                f"🆔 Transaction: {charge_id}"
            )
            return

        await user.upgrade_user_to_premium()
        await message.answer(
            f"🎉 Premium successfully activated!\n\n"
            f"✅ Unlimited channel aggregation unlocked\n"
            f"💰 Payment: {payment.total_amount} ⭐\n"
            f"🆔 Transaction: {charge_id}\n\n"
            f"Use /status to check your subscription!"
        )

    except Exception as e:
        logger.error(f"Payment processing error: {e}")
        await message.answer(
            f"❌ Error processing payment. Contact support.\n"
            f"Transaction: {message.successful_payment.telegram_payment_charge_id}"
        )
