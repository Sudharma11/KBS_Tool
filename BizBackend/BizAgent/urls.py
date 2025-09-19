# bizinsight/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

# URL patterns for the BizAgent application
urlpatterns = [
    path('', views.url_report_page, name='url_report_page'),  # This handles /url-report/
    path('api/url-report/', views.generate_url_report, name='generate_url_report'),  # This handles the API 
    path('api/pdf-report/', views.generate_pdf_report),
    path('api/download-docx/', views.download_docx),
    path('api/upload-pdf/', views.upload_pdf),
    path('api/file_check/', views.check_file_exists),
    # Two download routes
    path('api/download-docx/<str:report_type>/', views.download_docx, name='download_docx'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)