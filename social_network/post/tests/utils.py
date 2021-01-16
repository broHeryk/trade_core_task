from uuid import uuid1
from social_network.post.models import Post


def get_person_response(*_, **__):
    return {'person': {
        'name': {
            'givenName': 'Some',
            'familyName': 'Name'
            }
        }
    }


def build_user_payload(username, email=None, password=uuid1()):
    payload = {'username': username, 'password': password}
    if email:
        payload.update({'email': email})
    return payload


def create_post_for_user(user):
    post = Post(creator=user, data=uuid1())
    post.save()
    return post


def like_post(post, user):
    post.fans.add(user)
    post.save()


def build_post_payload(user_url):
    return {'data': 'some date', 'creator': user_url}
