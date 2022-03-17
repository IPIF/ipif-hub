from django.contrib import admin

from .models import Factoid, IpifRepo, Person, Place, Statement, Source, URI

admin.site.register(Factoid)
admin.site.register(IpifRepo)
admin.site.register(Person)
admin.site.register(Statement)
admin.site.register(Source)
admin.site.register(URI)
admin.site.register(Place)
