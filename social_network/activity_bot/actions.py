import itertools
import random
from logging import getLogger

logger = getLogger()


def sign_up_users(api_connector, config):
    users = []
    for user_number in range(config.number_of_users):
        users.append(api_connector.create_user())
    return users


def create_posts(users, api_connector, config):
    for user in users:
        api_connector.crate_posts_for_user(
            user=user,
            max_number=random.randint(1, config.max_posts_per_user)
        )


def perform_likes(user, users_with_no_likes, api_connector, config):
    available_likes = config.max_likes_per_user
    users = itertools.cycle(users_with_no_likes)
    while available_likes:
        user_with_unliked_posts = next(users)
        posts = api_connector.get_posts_for_user(
            target_user=user_with_unliked_posts,
            api_user=user)
        if not posts:
            continue
        api_connector.like_post(user, posts[random.randint(0, len(posts)-1)])
        available_likes -= 1


def like_posts(users, api_connector, config):
    # Sorted users by max number of posts
    users.sort(key=lambda u: len(u['posts']))
    while users:
        user = users.pop()
        api_connector.get_jwt_token(user)
        least_favorite_users = api_connector.get_users_with_no_likes(user)
        if not least_favorite_users:
            break
        perform_likes(user, least_favorite_users, api_connector, config)
