DEFAULT_LANGUAGE = 'eng'

MESSAGES = {
    'eng': {
        'start': '',
        'no_subscriptions': "You dont have any subscriptions. Type /subscribe to add some.",
        'subscriptions_list': 'Your subscriptions:\n\n{feed_list}'

    },
    'rus': {

    },
}


def get_message(key, language='en'):
    """
    Retrieve message by key and language with fallback to default language.

    Args:
        key (str): Message key
        language (str): Language code (default: 'en')

    Returns:
        str: Localized message or fallback message
    """
    if language in MESSAGES and key in MESSAGES[language]:
        return MESSAGES[language][key]
    elif key in MESSAGES[DEFAULT_LANGUAGE]:
        return MESSAGES[DEFAULT_LANGUAGE][key]
    else:
        return f"Message '{key}' not found"
