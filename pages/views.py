from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.generic import TemplateView
from .models import User


class HomePageView(TemplateView):
    template_name = 'inicio.html'


class MenuPageView(TemplateView):
    template_name = 'menu.html'


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')

        messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'login.html')


def signup_view(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip().lower()
        telefono = request.POST.get('telefono', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        if not nombre or not email or not password:
            messages.error(request, 'Completa todos los campos obligatorios.')
        elif password != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
        elif User.objects.filter(username=email).exists():
            messages.error(request, 'Ya existe una cuenta con ese correo.')
        else:
            User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=nombre,
                telefono=telefono,
            )
            messages.success(request, 'Cuenta creada exitosamente. Inicia sesión.')
            return redirect('login')

    return render(request, 'signup.html')


def logout_view(request):
    logout(request)
    return redirect('home')
