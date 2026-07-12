from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='portal/login.html', next_page='portal_dashboard'), name='portal_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='portal_login'), name='portal_logout'),
    path('', views.dashboard, name='portal_dashboard'),
    path('solicitar/', views.solicitar_servicio, name='portal_solicitar'),
    path('ordenes/crear/', views.crear_orden, name='portal_crear_orden'),
    path('ordenes/<int:pk>/', views.orden_detail, name='portal_orden_detail'),
    path('seguir/', views.seguir_ticket, name='portal_seguir'),
    path('comentar/<int:pk>/', views.comentar_ticket, name='portal_comentar'),
    path('oc/<int:pk>/', views.subir_oc, name='portal_subir_oc'),
    path('identificacion/<int:pk>/', views.subir_identificacion, name='portal_subir_identificacion'),
    path('pdf/<int:pk>/', views.ticket_pdf, name='portal_ticket_pdf'),
    path('herramientas/', views.herramientas, name='portal_herramientas'),
    path('descargar-script/', views.descargar_script, name='descargar_script'),
    path('descargar-bat/<int:pk>/', views.descargar_bat_ticket, name='descargar_bat_ticket'),
    path('cotizaciones/', views.portal_cotizaciones, name='portal_cotizaciones'),
    path('cotizaciones/<int:numero>/', views.portal_cotizacion_detail, name='portal_cotizacion_detail'),
    path('cotizaciones/<int:numero>/pdf/', views.cotizacion_pdf, name='portal_cotizacion_pdf'),
]
