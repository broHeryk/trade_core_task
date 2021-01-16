import threading

import clearbit
from django.contrib.auth.models import User
from django.conf import settings
from pyhunter import PyHunter
from rest_framework.serializers import ValidationError

from social_network.post.constants import HunterCodes

clearbit.key = settings.CLEARBIT_API_KEY
hunter = PyHunter(settings.HUNTER_API_KEY)


def verify_email(email):
    """Checks if email is valid and exists at all.
    :raises
        ValidationError -  if email address cant be reached"""

    try:
        response = hunter.email_verifier(email)
    except:
        # TODO: Verification does not work for now
        #  50 requests a month limit has been reached during testing. To make it work valid hunter key must be provided
        return
    if response.get('result') != HunterCodes.DELIVERABLE.value:
        raise ValidationError(f'Email {email} can not be reached ')


def fetch_name_data(email):
    if not email:
        return {}
    response = clearbit.Enrichment.find(email=email, stream=True)
    person = response['person']
    if not person:
        return {}
    name_data = person.get('name', {})
    # Could be extended in future but for now only first/second name is returned
    return {'first_name': name_data.get('givenName'), 'last_name': name_data.get('familyName')}


def populate_clearbit_user_data(user_id, email):
    name_data = fetch_name_data(email)
    user = User.objects.get(pk=user_id)
    if not name_data:
        return
    user.first_name = name_data['first_name']
    user.last_name = name_data['last_name']
    user.save()


def populate_clearbit_user_data_async(user_id, email):
    """ Running async retrieve of user data by email from clearbit"""
    return threading.Thread(target=populate_clearbit_user_data, args=(user_id, email)).start()
