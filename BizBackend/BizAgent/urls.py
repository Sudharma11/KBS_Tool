from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.url_report_page, name='url_report_page'),
    path('api/generate_report/', views.generate_url_report, name='generate_url_report'),
    path('api/upload_pdf/', views.upload_pdf, name='upload_pdf'),
    path('api/download/<str:filename>/', views.download_docx, name='download_docx'),
    # New URL for the scraper
    path('api/update-kanini-data/', views.update_kanini_data, name='update_kanini_data'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

