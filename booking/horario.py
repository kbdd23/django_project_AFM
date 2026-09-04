"""Horario de atencion del restaurante: la unica fuente de verdad.

Reglas del negocio (reflejadas en el pie de pagina del sitio):
- Lunes a viernes: 08:00 - 16:00
- Sabado:          09:00 - 15:00
- Domingo:         cerrado

Las reservas se hacen por bloques de exactamente 1 hora dentro de ese
rango: un bloque es (hora_inicio, hora_inicio + 1h).
"""

from datetime import datetime, time, timedelta

DURACION_BLOQUE = timedelta(hours=1)

# Indices de date.weekday(): lunes = 0 ... domingo = 6
ABRE_SEMANA = time(8, 0)
CIERRA_SEMANA = time(16, 0)
ABRE_SABADO = time(9, 0)
CIERRA_SABADO = time(15, 0)

DOMINGO = 6


def rango_atencion(fecha):
    """Devuelve (hora_apertura, hora_cierre) de una fecha, o None si cerrado."""
    if fecha.weekday() == DOMINGO:
        return None
    if fecha.weekday() == 5:  # sabado
        return ABRE_SABADO, CIERRA_SABADO
    return ABRE_SEMANA, CIERRA_SEMANA


def bloques_del_dia(fecha):
    """Bloques de 1 hora (inicio, fin) en que el restaurante atiende esa fecha.

    Una lista vacia significa que el restaurante esta cerrado.
    """
    rango = rango_atencion(fecha)
    if rango is None:
        return []

    apertura, cierre = rango
    bloques = []
    inicio = datetime.combine(fecha, apertura)
    cierre_dt = datetime.combine(fecha, cierre)

    while inicio + DURACION_BLOQUE <= cierre_dt:
        bloques.append((inicio.time(), (inicio + DURACION_BLOQUE).time()))
        inicio += DURACION_BLOQUE

    return bloques
