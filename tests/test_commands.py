from django.core.cache import cache
from django.core.management import call_command

class TestManagementCommands:

    def test_update_cache(self):
        assert cache.get('shib_ds') is None
        call_command('update_shib_ds_cache')
        assert cache.get('shib_ds') is not None
