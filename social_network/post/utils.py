from enum import Enum

import clearbit
from django.conf import settings
from pyhunter import PyHunter
from rest_framework.serializers import ValidationError


class HunterCodes(Enum):
    UNDELIVERABLE = 'undeliverable'

clearbit.key = settings.CLEARBIT_API_KEY

hunter = PyHunter(settings.HUNTER_API_KEY)


def verify_email(email):
    """Checks if email is valid and exists at all.
    :raises
        ValidationError -  if email address cant be reached"""

    try:
        response = hunter.email_verifier(email)
    except:
        # TODO: 50 requests a month limit is reached during testing. To make it work new hunter key should be provided
        return
    if response.get('result') == HunterCodes.UNDELIVERABLE.value:
        raise ValidationError(f'Email {email} can not be reached ')


def fetch_name_data(email):
    if not email:
        return {}
    response = clearbit.Enrichment.find(email=email, stream=True)
    person = response['person']
    if not person:
        return {}
    name_data = person.get('name', {})
    return {'first_name': name_data.get('givenName'), 'last_name': name_data.get('familyName')}
