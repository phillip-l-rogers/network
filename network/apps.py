from django.apps import AppConfig

from .signals import *


class NetworkConfig(AppConfig):
    name = "network"
