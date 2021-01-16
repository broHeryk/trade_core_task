import uuid

import requests
from django.conf import settings


class SocialApiConnector:
    # TODO: error handling for external requests and json decode
    def __init__(self):
        self.api_url = settings.API_URL
        self.posts_by_user_url = f'{self.api_url}api/posts/?creator={{id}}'
        self.create_user_url = f'{self.api_url}api/users/signup/'
        self.token_url = f'{self.api_url}api/token/'
        self.users_with_unliked_post_url = f'{self.api_url}api/users/least_favorite/'
        self.create_post_url = f'{self.api_url}api/posts/'

    def get_users_with_no_likes(self, user):
        response = self.request_with_jwt(user=user,
                                         data=None,
                                         method='get',
                                         url=self.users_with_unliked_post_url)
        return response.json()

    def create_user(self):
        payload = self.generate_user_payload()
        response = requests.post(self.create_user_url, json=payload)
        if response.status_code != 201:
            raise ValueError(response.json())
        payload.update(response.json())
        return payload

    def get_posts_for_user(self, target_user, api_user):
        if 'id' not in target_user:
            return []
        url = self.posts_by_user_url.format(id=target_user.get('id'))
        response = self.get_jwt_request(user=api_user, data=None, url=url)
        return response.json()

    def like_post(self, user, post):
        if not post:
            return
        url = post['url'] + 'like/'
        self.post_jwt_request(user=user, data=None, url=url)

    def get_jwt_token(self, user):
        response = requests.post(self.token_url, data={'username': user['username'], 'password': user['password']})
        user.update({'jwt_tokens': response.json()})

    def crate_posts_for_user(self, user, max_number):
        user['posts'] = []
        self.get_jwt_token(user)
        for _ in range(max_number):
            response = self.post_jwt_request(user=user,
                                             data=self.generate_post_payload(user),
                                             url=self.create_post_url)
            user['posts'].append(response.json())

    @staticmethod
    def post_jwt_request(user, data, url):
        return SocialApiConnector.request_with_jwt(user, data, 'post', url)

    @staticmethod
    def get_jwt_request(user, data, url):
        return SocialApiConnector.request_with_jwt(user, data, 'get', url)

    @staticmethod
    def request_with_jwt(user, data, method, url):
        jwt_auth_header = {'Authorization': f'Bearer {user["jwt_tokens"]["access"]}'}
        method = getattr(requests, method)
        return method(url, json=data, headers=jwt_auth_header)

    @staticmethod
    def generate_post_payload(user):
        return {'data': f'{user["username"]}: some date', 'creator': user['url']}

    @staticmethod
    def generate_user_payload():
        return {'username': str(uuid.uuid1()), 'password': str(uuid.uuid1()), 'email': 'support@soundmag.ua'}
