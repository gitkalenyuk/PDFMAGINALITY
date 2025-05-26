from django.contrib import admin
from .models import PdfDocument

@admin.register(PdfDocument)
class PdfDocumentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'user', 'upload_date', 'status')
    list_filter = ('status', 'user', 'upload_date')
    search_fields = ('file_name', 'user__username', 'user__email')
    readonly_fields = ('upload_date',)
