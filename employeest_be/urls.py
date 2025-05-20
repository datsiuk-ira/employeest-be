# employee_management_system/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Employee Management System API",
      default_version='v1',
      description="API documentation for the Employee Management System.\n"
                  "This system helps businesses track active projects and manage employees.\n"
                  "Features include company registration, employee management, project statistics, and task management.",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="admin@gmail.com"),
      license=openapi.License(name="Apache License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('api.urls')),

    # Swagger / OpenAPI schema paths
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Basic DRF auth URLs (for login/logout in browsable API)
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]