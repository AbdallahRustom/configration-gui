from django.urls import path
from .import views  


urlpatterns = [
    path ('',views.defaultweb, name='default'),
    path ('env/',views.env, name='env'),
    path ('apn/',views.apn, name='apn'),
    path('success/',views.success_view, name='success'),
    path('ipaddrerror/',views.ipaddrerror, name='ipaddrerror'),
    path('ipaddrdub/',views.ipaddrdub, name='ipaddrdub'),
    path('apndub/',views.apndub, name='apndub'),
    path('failedtodeploy/',views.failedtodeploy, name='failedtodeploy'),
    path('cdr/',views.cdr, name='cdr'),
]
