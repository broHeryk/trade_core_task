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


class ApiTest(TestCase):
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
        cls.api_user.delete()


@mock.patch('social_network.post.utils.populate_clearbit_user_data_async', mock.Mock())
@mock.patch('social_network.post.utils.verify_email', mock.Mock(side_effect=[ValidationError]))
class UserTest(ApiTest):

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

    def test_get_user(self):
        # Given: Already created user and stored in db
        self.assertTrue(User.objects.filter(username=self.username).exists())
        # When: Get user is called for existing user
        url = reverse('user-detail', args=(self.api_user.pk,))
        resp = self.api_client.get(url)
        # Then: 200 is returned
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        user_data = resp.json()
        # Then: Expected user returned in response
        self.assertEqual(user_data['username'], self.api_user.username)
        self.assertEqual(user_data['url'], f'http://testserver{url}')
        self.assertEqual(user_data['email'], self.api_user.email)
        self.assertEqual(user_data['first_name'], self.api_user.first_name)
        self.assertEqual(user_data['last_name'], self.api_user.last_name)
        self.assertEqual(user_data['id'], self.api_user.pk)

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
                response = method(url)
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PostTest(ApiTest):

    def setUp(self) -> None:
        self.post = test_utils.create_post_for_user(self.api_user)

    def tearDown(self):
        Post.objects.all().delete()

    def test_create_post(self):
        # Given: post payload
        payload = test_utils.build_post_payload(reverse('user-detail', args=(self.api_user.pk,)))
        # When: Authorized user send post
        self.api_client.post(reverse('post-list'), payload)
        # Then: The post is created and stored in db
        post = Post.objects.filter(data=payload['data']).first()
        self.assertTrue(post)

    def test_like_post(self):
        # Given: Post is created for user with no likes
        self.assertFalse(self.post.fans.all().count())
        # When: Like request is sent
        self.api_client.post(reverse('post-like', args=(self.post.pk,)))
        # Then: The user is added to the list of fans
        self.post.refresh_from_db()
        self.assertTrue(self.api_user in self.post.fans.all())

    def test_unlike_post(self):
        # Given: Post is created with no likes
        test_utils.like_post(self.post, self.api_user)
        # When: Unlike request is sent
        resp = self.api_client.post(reverse('post-unlike', args=(self.post.pk,)))
        # Then: 202 is returned
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        # Then: The user is removed from the list of fans
        self.post.refresh_from_db()
        self.assertFalse(self.post.fans.all().count())

    def test_unlike_post_not_liked_by_user_previously(self):
        # Given: The post is liked by a new user
        test_utils.like_post(
            self.post,
            user=User.objects.create_user(username="asdf",password="asdf")
        )
        # When: Unlike request is sent from user that has not liked the post
        resp = self.api_client.post(reverse('post-unlike', args=(self.post.pk,)))
        # Then: 403 is returned
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_posts_by_user(self):
        # Given: Post is created
        self.assertTrue(Post.objects.all().exists())
        # When: Filter request is sent with existing post owner
        resp = self.api_client.get(f'{reverse("post-list")}?creator={self.api_user.pk}')
        # Then: 200 is returned
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Then: 1 post item is returned in the list
        self.assertEqual(len(resp.json()), 1)

    def test_filter_posts_by_user_with_no_posts(self):
        # Given: Post is created
        user_id_with_no_posts = User.objects.create_user(username='asdf',password='asdf')
        # When: Filter request is sent for non existing user
        resp = self.api_client.get(f'{reverse("post-list")}?creator={user_id_with_no_posts}')
        # Then: 400 is returned
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_post(self):
        # Given:  Existing post in database
        self.assertTrue(Post.objects.get(pk=self.post.pk))
        # When: Filter request is sent for non existing user
        url = reverse("post-detail", args=(self.post.pk,))
        resp = self.api_client.get(url)
        # Then: 200 is returned
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        the_post = resp.json()
        self.assertEqual(the_post['data'], str(self.post.data))
        self.assertEqual(the_post['creator'], f'http://testserver{reverse("user-detail", args=(self.api_user.pk,))}')
        self.assertEqual(the_post['url'], f'http://testserver{url}')
        self.assertTrue('created_at' in the_post)
        self.assertEqual(the_post['fans'], [])

    def test_get_non_existing_post(self):
        # Given: post id does not exist
        post_id = 1000
        # When: post get request is called with id
        resp = self.api_client.get(reverse('post-detail', args=(post_id,)))
        # Then: 404 is returned
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthorized_requests(self):
        # Given: Api client with no token
        unauth_client = APIClient()
        # Given: list of urls to be reached
        urls = [(reverse('post-list'), unauth_client.get),
                (reverse('post-detail', args=(1,)), unauth_client.get),
                (reverse('post-like', args=(1,)), unauth_client.get),
                (reverse('post-unlike', args=(1,)), unauth_client.get)]
        for url, method in urls:
            with self.subTest(msg=f'Testing unauthorized request for{url}', url=url, method=method):
                response = method(url)
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
