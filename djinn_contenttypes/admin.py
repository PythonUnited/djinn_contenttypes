from django.contrib import admin
from djinn_contenttypes.models import FileAttachment, ImgAttachment

class AttachmentAdmin(admin.ModelAdmin):
    search_fields = ['title']

admin.site.register(FileAttachment, AttachmentAdmin)
admin.site.register(ImgAttachment, AttachmentAdmin)
