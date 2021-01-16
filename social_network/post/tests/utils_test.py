from unittest import mock
from social_network.post import utils
from social_network.post.tests import utils as test_utils
from social_network.post.constants import HunterCodes
import pytest
from django.contrib.auth.models import User
from rest_framework.serializers import ValidationError


@pytest.fixture(autouse=False)
def created_user():
    user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    return user


@mock.patch('social_network.post.utils.threading')
def test_populate_clearbit_user_data_async_called(threading_mock):
    # Given: user_id and email to process
    user_data = ('user_id', 'email')
    # When: populate_clearbit_user_data_async is called with user data
    utils.populate_clearbit_user_data_async(*user_data)
    # Then: A new thread with expected target function is created
    threading_mock.Thread.assert_called_once_with(target=utils.populate_clearbit_user_data, args=user_data)
    # Then: The thread is started
    assert threading_mock.Thread.return_value.start.call_count == 1


def test_fetch_name_data_with_no_email():
    # Given: email is empty string
    inval_email = ''
    # When: populate_clearbit_user_data is called with empty email
    result = utils.fetch_name_data(inval_email)
    # Then: Empty dictionary is returned
    assert result == {}


@mock.patch('clearbit.Enrichment.find', lambda *args, **kwargs: {'person': {}})
def test_fetch_name_data_when_no_person_returned():
    # Given: A valid email address but clearbit has no data by this email
    valid_email = 'not@empty.com'
    # When: populate_clearbit_user_data is called with the email
    result = utils.fetch_name_data(valid_email)
    # Then: Empty dictionary is returned
    assert result == {}


@mock.patch('clearbit.Enrichment.find', test_utils.get_person_response)
def test_fetch_name_data_when_person_data_is_returned():
    # Given: Person data is returned from clearbit
    person_data = test_utils.get_person_response()
    expected_res = {'first_name': person_data['person']['name']['givenName'],
                    'last_name': person_data['person']['name']['familyName']}
    # When: populate_clearbit_user_data is called with the email for existing user
    result = utils.fetch_name_data('no@matter.com')
    # Then: Data is unpacked properly into dict wiht name and surname
    assert result == expected_res


@pytest.mark.django_db
@mock.patch('clearbit.Enrichment.find', test_utils.get_person_response)
def test_populate_clearbit_user_data_successfully(created_user):
    clearbit_name = test_utils.get_person_response()['person']['name']
    # Given: Existing  user with no first name and no second name
    assert User.objects.all().count() == 1
    assert not created_user.first_name
    assert not created_user.last_name
    # When: populate_clearbit_user_data is called for the user
    utils.populate_clearbit_user_data(created_user.pk, created_user.email)
    created_user.refresh_from_db()
    # Then: username and password is updated for the user correctly
    assert (created_user.first_name, created_user.last_name) == (clearbit_name['givenName'], clearbit_name['familyName'])


@mock.patch('social_network.post.utils.hunter')
def test_verify_email_for_valid_address(hunter_mock):
    # Given: hunter returns valid email status for
    the_user = 'no@matter.com'
    hunter_mock.email_verifier = mock.Mock(return_value={'result': HunterCodes.DELIVERABLE.value})
    # When: verify email is called for the user
    utils.verify_email(the_user)
    # Then: no exception is thrown


@mock.patch('social_network.post.utils.hunter')
def test_verify_email_for_invalid_address(hunter_mock):
    # Given: hunter returns invalid email status for the user
    the_user = 'no@matter.com'
    hunter_mock.email_verifier = mock.Mock(return_value={'result': HunterCodes.UNDELIVERABLE.value})
    # When: verify email is called for the user
    with pytest.raises(ValidationError) as e:
        # Then: Validation error is thrown due to bad status
        utils.verify_email(the_user)

