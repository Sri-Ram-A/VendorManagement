from django.contrib import admin
from .models import Vendor, VendorDocument

# Register your models here.
admin.site.register(Vendor)
admin.site.register(VendorDocument)
