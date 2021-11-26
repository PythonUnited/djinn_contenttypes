from django.contrib import admin
from djinn_contenttypes.models import Category

from djinn_contenttypes.models import FileAttachment, ImgAttachment

class AttachmentAdmin(admin.ModelAdmin):
    search_fields = ['title']

admin.site.register(FileAttachment, AttachmentAdmin)
admin.site.register(ImgAttachment, AttachmentAdmin)


class CategoryAdmin(admin.ModelAdmin):

    prepopulated_fields = {"slug": ("name",)}


admin.site.register(Category, CategoryAdmin)
