from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .horario import bloques_del_dia
from .models import Mesa, Reserva


class ReservaForm(forms.ModelForm):
    """Formulario de reserva: el cliente elige mesa, fecha y bloque horario.

    El cliente (usuario autenticado) no aparece en el form: lo impone el
    servidor desde request.user en la vista. El estado nace siempre 'confirmado'.
    """

    class Meta:
        model = Reserva
        fields = ['mesa', 'fecha', 'hora_inicio', 'hora_fin']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El cliente solo ve mesas en servicio; la disponibilidad real la
        # decide la BD en clean(), contra las reservas confirmadas.
        self.fields['mesa'].queryset = Mesa.objects.filter(activa=True)

    def clean(self):
        # Se ejecuta automaticamente cuando la vista llama a is_valid().
        # super().clean() corre primero el clean() del modelo (hora_fin > hora_inicio).
        datos = super().clean()
        mesa = datos.get('mesa')
        fecha = datos.get('fecha')
        hora_inicio = datos.get('hora_inicio')
        hora_fin = datos.get('hora_fin')

        if fecha:
            self._validar_fecha(fecha, hora_inicio)

        if mesa and fecha and hora_inicio and hora_fin:
            self._validar_bloque(fecha, hora_inicio, hora_fin)
            if Reserva.solapamiento(mesa, fecha, hora_inicio, hora_fin).exists():
                raise ValidationError('Esa mesa ya esta reservada en ese horario.')
        return datos

    def _validar_fecha(self, fecha, hora_inicio):
        """Reglas de dominio sobre la fecha: pasado, cerrado y bloques vencidos."""
        hoy = timezone.localdate()
        if fecha < hoy:
            raise ValidationError('No puedes reservar para una fecha pasada.')

        if not bloques_del_dia(fecha):
            raise ValidationError('El restaurante esta cerrado ese dia.')

        # El bloque que ya empezo hoy no se puede reservar.
        if fecha == hoy and hora_inicio and hora_inicio <= timezone.localtime().time():
            raise ValidationError('Ese bloque ya comenzo, elige una hora futura.')

    def _validar_bloque(self, fecha, hora_inicio, hora_fin):
        """La reserva debe ser un rango continuo de bloques de 1 hora.

        Un rango valido empieza donde empieza un bloque y termina donde
        termina otro: (10:00-12:00) cubre dos bloques; (10:00-11:00)
        cubre uno. Como el horario es continuo (sin recesos), alinear
        ambos extremos a los bloques del dia garantiza que no hay huecos
        internos. hora_fin > hora_inicio ya lo valida el clean() del modelo.
        """
        bloques = bloques_del_dia(fecha)
        inicios = {inicio for inicio, _ in bloques}
        fines = {fin for _, fin in bloques}
        if hora_inicio not in inicios or hora_fin not in fines:
            raise ValidationError('Elige un rango completo de bloques dentro del horario de atencion.')
