from django.urls import path
from pages.views import (
    HomePageView,
    MenuPageView,
    login_view,
    signup_view,
    logout_view,
    perfil_view,
)

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('menu/', MenuPageView.as_view(), name='menu'),
    path('login/', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', logout_view, name='logout'),
    path('perfil/', perfil_view, name='perfil'),
]
