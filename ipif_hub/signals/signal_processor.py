from django.db import models
from haystack import signals


class SignalProcessor(signals.BaseSignalProcessor):
    def setup(self):
        # Naive (listen to all model saves).
        # models.signals.post_save.connect(self.handle_save)
        models.signals.post_delete.connect(self.handle_delete)
        # Efficient would be going through all backends & collecting all models
        # being used, then hooking up signals only for those.

    def teardown(self):
        # Naive (listen to all model saves).
        # models.signals.post_save.disconnect(self.handle_save)
        models.signals.post_delete.disconnect(self.handle_delete)
        # Efficient would be going through all backends & collecting all models
        # being used, then disconnecting signals only for those.
