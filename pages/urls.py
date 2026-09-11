from django.urls import path

from pages.views import (
    HomePageView,
    MenuPageView,
    login_view,
    signup_view,
    logout_view,
    perfil_view,
    mesero_view,
    mesas_estado,
    tomar_mesa,
    orden_agregar,
    orden_quitar,
    orden_cerrar,
)

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('menu/', MenuPageView.as_view(), name='menu'),
    path('login/', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', logout_view, name='logout'),
    path('perfil/', perfil_view, name='perfil'),
    path('mesero/', mesero_view, name='mesero'),
    path('mesero/mesas/', mesas_estado, name='mesas_estado'),
    path('mesero/tomar/', tomar_mesa, name='tomar_mesa'),
    path('mesero/orden/agregar/', orden_agregar, name='orden_agregar'),
    path('mesero/orden/quitar/', orden_quitar, name='orden_quitar'),
    path('mesero/orden/cerrar/', orden_cerrar, name='orden_cerrar'),
]
