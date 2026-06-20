from django.contrib import admin
from .models import Vendor,VendorAccessGrant,VendorDocument

# Register your models here.
admin.site.register(Vendor)
admin.site.register(VendorDocument)
admin.site.register(VendorAccessGrant)
