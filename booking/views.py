from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_GET

from .forms import ReservaForm
from .horario import bloques_del_dia
from .models import Mesa, Reserva


@login_required
def crear_reserva(request):
    """Alta de reserva: solo usuarios autenticados.

    El cliente nunca viene del navegador: el servidor lo impone desde
    request.user. El formulario valida formato, rango y solapamiento.
    """
    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)
            reserva.cliente = request.user
            reserva.save()
            messages.success(
                request,
                f'Reserva confirmada: Mesa {reserva.mesa.numero} el '
                f'{reserva.fecha} de {reserva.hora_inicio} a {reserva.hora_fin}.',
            )
            return redirect('booking:crear_reserva')
    else:
        form = ReservaForm()

    # El salon vivo: las mesas del modelo, no un HTML hardcodeado.
    mesas = Mesa.objects.filter(activa=True).order_by('numero')

    # related_name='reservas' del FK cliente -> request.user.reservas
    reservas_usuario = request.user.reservas.order_by('-fecha', '-hora_inicio')

    return render(
        request,
        'reserva_form.html',
        {'form': form, 'mesas': mesas, 'reservas_usuario': reservas_usuario},
    )


@login_required
@require_GET
def bloques_disponibles(request):
    """Disponibilidad de una mesa para una fecha, en bloques de 1 hora.

    Es la pregunta que el navegador hace ANTES de mostrar el formulario:
    GET /reservar/bloques/?mesa=<pk>&fecha=YYYY-MM-DD
    Devuelve cada bloque del horario con su estado libre/ocupado, calculado
    contra las reservas confirmadas en la BD (Reserva.solapamiento).
    """
    try:
        mesa = Mesa.objects.get(pk=request.GET.get('mesa'), activa=True)
        fecha = datetime.strptime(request.GET.get('fecha'), '%Y-%m-%d').date()
    except (Mesa.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'error': 'Mesa o fecha invalidas.'}, status=400)

    hoy = timezone.localdate()
    if fecha < hoy:
        return JsonResponse({'error': 'La fecha ya paso.'}, status=400)

    bloques = bloques_del_dia(fecha)
    if not bloques:
        return JsonResponse({'error': 'El restaurante esta cerrado ese dia.'}, status=400)

    # De hoy en adelante solo se ofrecen bloques que aun no comienzan.
    if fecha == hoy:
        ahora = timezone.localtime().time()
        bloques = [(inicio, fin) for inicio, fin in bloques if inicio > ahora]

    respuesta = []
    for inicio, fin in bloques:
        ocupado = Reserva.solapamiento(mesa, fecha, inicio, fin).exists()
        respuesta.append({
            'inicio': inicio.strftime('%H:%M'),
            'fin': fin.strftime('%H:%M'),
            'libre': not ocupado,
        })

    return JsonResponse({
        'mesa': mesa.numero,
        'fecha': fecha.isoformat(),
        'bloques': respuesta,
    })
