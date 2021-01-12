import logging
import os
from collections import namedtuple

import yaml
from django.core.management.base import BaseCommand

from social_network.activity_bot.actions import (create_posts, like_posts,
                                                 sign_up_users)
from social_network.activity_bot.social_network_client import \
    SocialApiConnector

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class Command(BaseCommand):
    help = 'Run social network activity simulation'

    def add_arguments(self, parser):
        parser.add_argument('bot_config_file_path', nargs='+', type=str)

    def handle(self, *args, **options):
        bot_config = self.read_bot_config_file(options['bot_config_file_path'][0])
        api_connector = SocialApiConnector()
        logger.info('Start activity process')
        logger.info('Start creation of users')
        users = sign_up_users(api_connector, bot_config)
        logger.info('Start creation of posts')
        create_posts(users, api_connector, bot_config)
        logger.info('Start performing likes all posts')
        like_posts(users, api_connector, bot_config)
        logger.info('Activity simulation is finished')

    @staticmethod
    def read_bot_config_file(config_file_path):
        if not os.path.isfile(config_file_path):
            raise FileNotFoundError(f'Config file path must be specified correctly. {config_file_path} is not valid.')

        Config = namedtuple('Config', ['number_of_users', 'max_posts_per_user', 'max_likes_per_user'])
        with open(config_file_path) as file:
            # TODO: error handling while for invalid formats
            config_yml = yaml.load(file, Loader=yaml.FullLoader)
            return Config(**config_yml)

