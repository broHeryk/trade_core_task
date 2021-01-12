# Project
The social_network project is test assessment and created only for self using
purposes.
Project is simple REST api that allows creation users and posts.

For using of django app you must setup secrets for hunter(https://hunter.io/) and clearbit(https://dashboard.clearbit.com/).

# Installation/Configuration
- Pull the repo
- Setup virtualenv in any preferable way
- Install requirements like:
    pip install -r requirements.txt
- Set up clearbit and hunter api keys into HUNTER_API_KEY CLEARBIT_API_KEY in social_network/settings.py
- (*Optional*) If app will be working with non-default host and port then API_URL environment variable must be set up
- (*Optional*) Configure bot_config.yml to change default activity bot settings


# Running
- to start django REST api:
    - python manage.py runserver
- to run activity bot:
    - python manage.py simulate_activity <path_to_config_yaml_file>