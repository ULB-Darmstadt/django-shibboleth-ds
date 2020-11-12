from django.core.management.base import BaseCommand

from shibboleth_discovery.utils import set_cache

class Command(BaseCommand):
    help = "Updates the cache with the new data from DiscoFeed"

    def handle(self, *args, **options):
        set_cache()
