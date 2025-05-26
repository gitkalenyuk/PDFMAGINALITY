from django.urls import path
from . import views

urlpatterns = [
    path('upload', views.upload_pdf, name='upload_pdf'),
    path('<int:document_id>/extract-text', views.extract_pdf_text_view, name='extract_pdf_text'),
    path('<int:document_id>/identify-prices', views.identify_prices_view, name='identify_prices'),
    path('<int:document_id>/ocr-region', views.ocr_text_from_region_view, name='ocr_text_from_region'),
    path('<int:document_id>/analyze-style-region', views.analyze_text_style_view, name='analyze_text_style'),
    path('<int:document_id>/replace-text-region', views.replace_text_region_view, name='replace_text_region'),
    path('<int:document_id>/download', views.download_modified_pdf_view, name='download_modified_pdf'),
    path('documents', views.list_user_documents_view, name='list_user_documents'),
    path('<int:document_id>/delete', views.delete_document_view, name='delete_document'),
]
