from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ReservaForm
from .horario import bloques_del_dia
from .models import Mesa, Reserva

User = get_user_model()


def crear_mesa(numero=1, capacidad=4, ubicacion='salon central', es_grande=False):
    return Mesa.crear_mesa(
        numero=numero,
        capacidad=capacidad,
        ubicacion=ubicacion,
        es_grande=es_grande,
    )


def proximo_lunes():
    """Proxima fecha lunes (futura): los tests no dependen del dia en que corran."""
    hoy = date.today()
    delta = (0 - hoy.weekday()) % 7
    return hoy + timedelta(days=delta if delta else 7)


def proximo_sabado():
    hoy = date.today()
    delta = (5 - hoy.weekday()) % 7
    return hoy + timedelta(days=delta if delta else 7)


def proximo_domingo():
    hoy = date.today()
    delta = (6 - hoy.weekday()) % 7
    return hoy + timedelta(days=delta)


class HorarioTests(SimpleTestCase):
    """El horario real del restaurante: L-V 08-16, Sab 09-15, Dom cerrado.

    SimpleTestCase: logica pura, sin base de datos (no hay que crear la
    base de test remota solo para sumar horas).
    """

    def test_lunes_tiene_8_bloques_de_una_hora(self):
        bloques = bloques_del_dia(proximo_lunes())
        self.assertEqual(len(bloques), 8)
        self.assertEqual(bloques[0], (time(8, 0), time(9, 0)))
        self.assertEqual(bloques[-1], (time(15, 0), time(16, 0)))

    def test_sabado_tiene_6_bloques(self):
        self.assertEqual(len(bloques_del_dia(proximo_sabado())), 6)

    def test_domingo_esta_cerrado(self):
        self.assertEqual(bloques_del_dia(proximo_domingo()), [])


class FormularioReservaTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username='fran@test.cl', email='fran@test.cl', password='clave-segura'
        )
        self.mesa = crear_mesa(numero=1)

    def test_form_valido_para_bloque_del_horario(self):
        formulario = ReservaForm(data={
            'mesa': self.mesa.pk,
            'fecha': proximo_lunes(),
            'hora_inicio': '10:00',
            'hora_fin': '11:00',
        })
        self.assertTrue(formulario.is_valid(), formulario.errors)

    def test_rechaza_domingo(self):
        formulario = ReservaForm(data={
            'mesa': self.mesa.pk,
            'fecha': proximo_domingo(),
            'hora_inicio': '10:00',
            'hora_fin': '11:00',
        })
        self.assertFalse(formulario.is_valid())

    def test_rechaza_bloque_fuera_del_horario(self):
        formulario = ReservaForm(data={
            'mesa': self.mesa.pk,
            'fecha': proximo_lunes(),
            'hora_inicio': '17:00',
            'hora_fin': '18:00',
        })
        self.assertFalse(formulario.is_valid())

    def test_acepta_rango_de_dos_bloques_consecutivos(self):
        formulario = ReservaForm(data={
            'mesa': self.mesa.pk,
            'fecha': proximo_lunes(),
            'hora_inicio': '10:00',
            'hora_fin': '12:00',
        })
        self.assertTrue(formulario.is_valid(), formulario.errors)

    def test_acepta_rango_largo_de_varios_bloques(self):
        formulario = ReservaForm(data={
            'mesa': self.mesa.pk,
            'fecha': proximo_lunes(),
            'hora_inicio': '10:00',
            'hora_fin': '15:00',
        })
        self.assertTrue(formulario.is_valid(), formulario.errors)

    def test_rechaza_inicio_no_alineado_a_un_bloque(self):
        formulario = ReservaForm(data={
            'mesa': self.mesa.pk,
            'fecha': proximo_lunes(),
            'hora_inicio': '10:30',
            'hora_fin': '11:30',
        })
        self.assertFalse(formulario.is_valid())

    def test_rechaza_fin_no_alineado_a_un_bloque(self):
        formulario = ReservaForm(data={
            'mesa': self.mesa.pk,
            'fecha': proximo_lunes(),
            'hora_inicio': '10:00',
            'hora_fin': '11:30',
        })
        self.assertFalse(formulario.is_valid())

    def test_rechaza_bloque_que_ya_comenzo_hoy(self):
        hoy = timezone.localdate()
        with (
            patch('booking.forms.timezone.localdate', return_value=hoy),
            patch('booking.forms.timezone.localtime', return_value=datetime.combine(hoy, time(12, 0))),
        ):
            formulario = ReservaForm(data={
                'mesa': self.mesa.pk,
                'fecha': hoy,
                'hora_inicio': '10:00',
                'hora_fin': '11:00',
            })
        self.assertFalse(formulario.is_valid())

    def test_no_ofrece_mesas_retiradas(self):
        retirada = crear_mesa(numero=2)
        retirada.retirar()
        formulario = ReservaForm()
        self.assertNotIn(retirada.pk, formulario.fields['mesa'].queryset.values_list('pk', flat=True))


class VistaCrearReservaTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username='fran@test.cl', email='fran@test.cl', password='clave-segura'
        )
        self.mesa = crear_mesa(numero=1)
        self.url = reverse('booking:crear_reserva')

    def test_requiere_login(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('login'), respuesta.url)

    def test_contexto_solo_con_mesas_activas(self):
        retirada = crear_mesa(numero=2)
        retirada.retirar()
        self.client.force_login(self.usuario)
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(list(respuesta.context['mesas']), [self.mesa])

    def test_post_crea_reserva_ligada_al_usuario(self):
        self.client.force_login(self.usuario)
        fecha = proximo_lunes()
        respuesta = self.client.post(self.url, {
            'mesa': self.mesa.pk,
            'fecha': fecha,
            'hora_inicio': '10:00',
            'hora_fin': '11:00',
        })
        self.assertRedirects(respuesta, self.url)
        reserva = Reserva.objects.get()
        self.assertEqual(reserva.cliente, self.usuario)
        self.assertEqual(reserva.mesa, self.mesa)

    def test_post_crea_reserva_de_rango_multibloque(self):
        self.client.force_login(self.usuario)
        fecha = proximo_lunes()
        respuesta = self.client.post(self.url, {
            'mesa': self.mesa.pk,
            'fecha': fecha,
            'hora_inicio': '10:00',
            'hora_fin': '13:00',
        })
        self.assertRedirects(respuesta, self.url)
        reserva = Reserva.objects.get()
        self.assertEqual(reserva.cliente, self.usuario)
        self.assertEqual(reserva.hora_inicio, time(10, 0))
        self.assertEqual(reserva.hora_fin, time(13, 0))

    def test_post_rechaza_solapamiento(self):
        self.client.force_login(self.usuario)
        fecha = proximo_lunes()
        Reserva.objects.create(
            cliente=self.usuario, mesa=self.mesa,
            fecha=fecha, hora_inicio=time(10, 0), hora_fin=time(11, 0),
        )
        # Un rango de 10:00-12:00 cubre el bloque 10:00-11:00 ya reservado.
        respuesta = self.client.post(self.url, {
            'mesa': self.mesa.pk,
            'fecha': fecha,
            'hora_inicio': '10:00',
            'hora_fin': '12:00',
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Esa mesa ya esta reservada en ese horario.')


class VistaBloquesDisponiblesTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username='fran@test.cl', email='fran@test.cl', password='clave-segura'
        )
        self.mesa = crear_mesa(numero=1)
        self.url = reverse('booking:bloques')
        self.fecha_lunes = proximo_lunes()

    def parametros(self, mesa=None, fecha=None):
        return {
            'mesa': (mesa or self.mesa).pk,
            'fecha': fecha or self.fecha_lunes,
        }

    def test_requiere_login(self):
        respuesta = self.client.get(self.url, self.parametros())
        self.assertEqual(respuesta.status_code, 302)

    def test_devuelve_8_bloques_libres_un_lunes(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(self.url, self.parametros())
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertEqual(len(datos['bloques']), 8)
        self.assertTrue(all(bloque['libre'] for bloque in datos['bloques']))

    def test_marca_ocupado_el_bloque_reservado(self):
        Reserva.objects.create(
            cliente=self.usuario, mesa=self.mesa,
            fecha=self.fecha_lunes, hora_inicio=time(10, 0), hora_fin=time(11, 0),
        )
        self.client.force_login(self.usuario)
        datos = self.client.get(self.url, self.parametros()).json()
        bloque_10 = next(b for b in datos['bloques'] if b['inicio'] == '10:00')
        self.assertFalse(bloque_10['libre'])
        self.assertEqual(sum(1 for b in datos['bloques'] if b['libre']), 7)

    def test_reserva_multibloque_ocupa_todos_sus_bloques(self):
        Reserva.objects.create(
            cliente=self.usuario, mesa=self.mesa,
            fecha=self.fecha_lunes, hora_inicio=time(10, 0), hora_fin=time(13, 0),
        )
        self.client.force_login(self.usuario)
        datos = self.client.get(self.url, self.parametros()).json()
        ocupados = [b['inicio'] for b in datos['bloques'] if not b['libre']]
        self.assertEqual(ocupados, ['10:00', '11:00', '12:00'])
        self.assertEqual(sum(1 for b in datos['bloques'] if b['libre']), 5)

    def test_domingo_devuelve_400(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(self.url, self.parametros(fecha=proximo_domingo()))
        self.assertEqual(respuesta.status_code, 400)

    def test_mesa_retirada_devuelve_400(self):
        retirada = crear_mesa(numero=2)
        retirada.retirar()
        self.client.force_login(self.usuario)
        respuesta = self.client.get(self.url, self.parametros(mesa=retirada))
        self.assertEqual(respuesta.status_code, 400)

    def test_fecha_pasada_devuelve_400(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(self.url, self.parametros(fecha=date.today() - timedelta(days=1)))
        self.assertEqual(respuesta.status_code, 400)

    def test_hoy_solo_ofrece_bloques_futuros(self):
        hoy = timezone.localdate()
        with (
            patch('booking.views.timezone.localdate', return_value=hoy),
            patch('booking.views.timezone.localtime', return_value=datetime.combine(hoy, time(12, 0))),
        ):
            self.client.force_login(self.usuario)
            datos = self.client.get(self.url, self.parametros(fecha=hoy)).json()
        inicios = [bloque['inicio'] for bloque in datos['bloques']]
        self.assertNotIn('08:00', inicios)
        self.assertIn('13:00', inicios)
