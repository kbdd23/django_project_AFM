from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from booking.models import Mesa, Reserva

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


TABS_DEL_PANEL = ('inicio', 'reservar', 'historial', 'perfil')


@login_required
def perfil_view(request):
    """Panel del cliente: una sola URL y el tab viaja como parametro.

    ?tab=inicio|reservar|historial|perfil. En vez de una URL por seccion,
    el servidor entrega unicamente los datos de la seccion pedida: el
    template decide que mostrar, la vista decide que consultar.
    """
    tab = request.GET.get('tab', 'inicio')
    if tab not in TABS_DEL_PANEL:
        tab = 'inicio'

    if request.method == 'POST' and tab == 'perfil':
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        # El correo no se toca: es el username con el que se hace login.
        request.user.first_name = nombre
        request.user.telefono = telefono
        request.user.save(update_fields=['first_name', 'telefono'])
        messages.success(request, 'Datos actualizados.')
        return redirect(f"{reverse('perfil')}?tab=perfil")

    hoy = timezone.localdate()
    contexto = {'tab': tab}

    if tab == 'inicio':
        contexto['proximas_reservas'] = (
            request.user.reservas
            .filter(estado=Reserva.ESTADO_CONFIRMADO, fecha__gte=hoy)
            .select_related('mesa')
            .order_by('fecha', 'hora_inicio')
        )
    elif tab == 'reservar':
        contexto['mesas'] = Mesa.objects.filter(activa=True).order_by('numero')
    elif tab == 'historial':
        contexto['historial'] = (
            request.user.reservas
            .filter(
                Q(estado=Reserva.ESTADO_CANCELADO)
                | Q(estado=Reserva.ESTADO_CONFIRMADO, fecha__lt=hoy)
            )
            .select_related('mesa')
            .order_by('-fecha', '-hora_inicio')
        )

    return render(request, 'dashboard_cliente.html', contexto)
