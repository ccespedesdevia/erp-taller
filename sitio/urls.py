from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='sitio_home'),
    path('servicios/', views.servicio_list, name='sitio_servicios'),
    path('servicios/<slug:slug>/', views.servicio_detail, name='sitio_servicio'),
    path('blog/', views.blog_list, name='sitio_blog'),
    path('blog/<slug:slug>/', views.blog_detail, name='sitio_blog_article'),
    path('enviar-contacto/', views.enviar_contacto, name='sitio_enviar_contacto'),
]
