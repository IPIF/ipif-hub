from django.contrib import admin

from .models import (
    URI,
    Factoid,
    IpifRepo,
    MergePerson,
    MergeSource,
    Person,
    Place,
    Source,
    Statement,
)

admin.site.register(Factoid)
admin.site.register(IpifRepo)
admin.site.register(Person)
admin.site.register(Statement)
admin.site.register(Source)
admin.site.register(URI)
admin.site.register(Place)
admin.site.register(MergePerson)
admin.site.register(MergeSource)
