from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='portal/login.html', next_page='portal_dashboard'), name='portal_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='portal_login'), name='portal_logout'),
    path('', views.dashboard, name='portal_dashboard'),
    path('ordenes/crear/', views.crear_orden, name='portal_crear_orden'),
    path('ordenes/<int:pk>/', views.orden_detail, name='portal_orden_detail'),
    path('seguir/', views.seguir_ticket, name='portal_seguir'),
]
