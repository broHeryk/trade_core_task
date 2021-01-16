import os
import sys
import pytest


if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'social_network.settings.test'

if __name__ == '__main__':
    sys.exit(pytest.main())