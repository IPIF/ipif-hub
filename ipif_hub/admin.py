from django.contrib import admin

from .models import URI, Factoid, IpifRepo, Person, Place, Source, Statement

admin.site.register(Factoid)
admin.site.register(IpifRepo)
admin.site.register(Person)
admin.site.register(Statement)
admin.site.register(Source)
admin.site.register(URI)
admin.site.register(Place)
