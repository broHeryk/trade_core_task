
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User

from social_network.post.tests import utils as test_utils
from social_network.post.models import Post
from django.test import TestCase
from unittest import mock
from rest_framework.serializers import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from social_network.post.views import UserViewSet

@mock.patch('social_network.post.utils.populate_clearbit_user_data_async', mock.Mock())
@mock.patch('social_network.post.utils.verify_email', mock.Mock(side_effect=[ValidationError]))
class UserTest(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.api_client = APIClient()
        cls.username = 'Bob'
        cls.password = 'super12345678'
        cls.api_user = User.objects.create_user(cls.username, 'a@b.com', cls.password)
        refresh = RefreshToken.for_user(cls.api_user)
        cls.api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def setUp(self) -> None:
        pass
    def tearDown(self) -> None:
        pass

    def test_user_creation(self):
        # Given: user with username to be created
        username = 'HarryPovar'
        payload = test_utils.build_user_payload(username)
        # When: post request is called with user payload
        resp = self.api_client.post(reverse('user-signup'), data=payload)
        # Then: 201 is returned
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # Then: The user is created and exists in the database
        self.assertTrue(User.objects.filter(username=username).exists())

    @mock.patch('social_network.post.utils.verify_email', mock.Mock(side_effect=[ValidationError]))
    def test_user_creation_with_invalid_mail(self):
        # Given: user with username to be created
        username = 'HarryPovar'
        # Given: Hunter returns unreachable status for the user
        payload = test_utils.build_user_payload(username, email='poc@poc.com')
        # When: post request is called with user payload
        resp = self.api_client.post(reverse('user-signup'), data=payload)
        # Then: 400 bad request is returned
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        # Then: No user is created with this username
        self.assertFalse(User.objects.filter(username=username).exists())

    def test_create_user_with_existing_username(self):
        # Given: Already created user with username
        self.assertTrue(User.objects.filter(username=self.username).exists())
        payload = test_utils.build_user_payload(self.username)
        # When: post request is called with the already existing username
        resp = self.api_client.post(reverse('user-signup'), data=payload)
        # Then: 400 bad request is returned
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user(self):
        # Given: Already created user and stored in db
        self.assertTrue(User.objects.filter(username=self.username).exists())
        # When: Get user is called for existing user
        resp = self.api_client.get(reverse('user-detail', args=(self.api_user.pk,)))
        # Then: 200 is returned
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Then: Expected user returned in response
        self.assertEqual(resp.json()['username'], self.username)

    def test_retrieve_non_existing_user(self):
        # Given: Non existing user id
        usr_id = 300
        self.assertFalse(User.objects.filter(pk=usr_id).exists())
        # When: get user is called with non existing id
        resp = self.api_client.get(reverse('user-detail', args=(usr_id,)))
        # Then: 404 is returned
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_user_with_no_likes_when_all_users_have_liked_posts(self):
        # Given: User with created post
        post = test_utils.create_post_for_user(self.api_user)
        # Given: post is liked
        test_utils.like_post(post, self.api_user)
        # When: least_favorite view is called
        resp = self.api_client.get(reverse('user-least-favorite'))
        # Then: 200 empty response is returned
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json(), [])

    def test_get_user_with_no_likes(self):
        # Given: User with created post
        post = test_utils.create_post_for_user(self.api_user)
        # Given: post has no likes
        self.assertEqual(post.fans.count(), 0)
        # When: least_favorite view is called
        resp = self.api_client.get(reverse('user-least-favorite'))
        # Then: 200 is returned
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Then: The owner of unliked post is returned in the list of users
        self.assertEqual(resp.json()[0]['username'], self.username)

    def test_unauthorized_access(self):
        # Given: Api client with no token
        unauth_client = APIClient()
        # Given: list of urls to be reached
        urls = [(reverse('user-list'), unauth_client.get),
                (reverse('user-detail', args=(1,)), unauth_client.get),
                (reverse('user-least-favorite'), unauth_client.get)]
        for url, method in urls:
            with self.subTest(msg=f'Testing unauthorized request for{url}', url=url, method=method):
                response=method(url)
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
