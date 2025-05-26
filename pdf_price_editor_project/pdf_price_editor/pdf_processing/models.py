from django.db import models
from django.contrib.auth.models import User
import os

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/pdfs/<filename>
    # Ensure filename is just the base name to prevent path traversal issues
    filename = os.path.basename(filename)
    return f'user_{instance.user.id}/pdfs/{filename}'

class PdfDocument(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pdf_documents')
    file_name = models.CharField(max_length=255, blank=True) # Allow blank as it will be set in save
    uploaded_file = models.FileField(upload_to=user_directory_path)
    upload_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploaded'
    )
    extracted_text = models.TextField(blank=True, null=True)
    modified_file = models.FileField(upload_to=user_directory_path, blank=True, null=True) # Field for modified PDF

    def __str__(self):
        return f"{self.file_name or 'Unnamed PDF'} by {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.file_name and self.uploaded_file:
            self.file_name = os.path.basename(self.uploaded_file.name)
        super().save(*args, **kwargs)
