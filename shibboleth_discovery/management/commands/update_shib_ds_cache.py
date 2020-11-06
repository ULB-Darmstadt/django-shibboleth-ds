from django.core.management.base import BaseCommand

from django.conf import settings
from django.core.cache import cache

from shibboleth_discovery.utils import prepare_data

class Command(BaseCommand):
    help = "Updates the cache with the new data from DiscoFeed"

    def handle(self, *args, **options):
        cache.set(
            'shib_ds',
            prepare_data(),
            timeout=settings.SHIB_DS_CACHE_DURATION
        )

