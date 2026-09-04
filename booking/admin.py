from django.contrib import admin
from .models import Mesa, Reserva


@admin.action(description='Retirar del salon (soft delete)')
def retirar_mesas(modeladmin, request, queryset):
    for mesa in queryset:
        mesa.retirar()


@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'capacidad', 'ubicacion', 'es_grande', 'activa']
    list_filter = ['activa', 'ubicacion']
    actions = [retirar_mesas]


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'mesa', 'fecha', 'hora_inicio', 'hora_fin', 'estado']
    list_filter = ['estado', 'fecha']
    date_hierarchy = 'fecha'
