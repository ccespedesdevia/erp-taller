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
    path('comentar/<str:codigo>/', views.comentar_ticket, name='portal_comentar'),
    path('oc/<str:codigo>/', views.subir_oc, name='portal_subir_oc'),
    path('identificacion/<str:codigo>/', views.subir_identificacion, name='portal_subir_identificacion'),
    path('pdf/<str:codigo>/', views.ticket_pdf, name='portal_ticket_pdf'),
    path('herramientas/', views.herramientas, name='portal_herramientas'),
    path('descargar-script/', views.descargar_script, name='descargar_script'),
    path('descargar-bat/<str:codigo>/', views.descargar_bat_ticket, name='descargar_bat_ticket'),
    path('cotizaciones/', views.portal_cotizaciones, name='portal_cotizaciones'),
    path('cotizaciones/<int:numero>/', views.portal_cotizacion_detail, name='portal_cotizacion_detail'),
    path('cotizaciones/<int:numero>/pdf/', views.cotizacion_pdf, name='portal_cotizacion_pdf'),
    path('chat/', views.chat_inicio, name='portal_chat_inicio'),
    path('chat/<uuid:session_id>/', views.chat_ver, name='portal_chat_ver'),
    path('chat/<uuid:session_id>/api/', views.chat_api, name='portal_chat_api'),
    path('chat/<uuid:session_id>/crear/', views.chat_crear_ticket, name='portal_chat_crear'),
]
