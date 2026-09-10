"""nuke.py - Deja la base de datos de desarrollo en cero.

No es parte del flujo de la aplicacion: existe para depurar cuando los
datos de prueba estorban (migraciones sucias, mesas duplicadas, reservas
de prueba encadenadas, usuarios basura, etc).

Uso:
    python nuke.py          vacia los documentos de todas las colecciones
    python nuke.py --drop   elimina la base completa (hay que migrar de nuevo)
    python nuke.py --si     omite la confirmacion interactiva

Las credenciales se leen de settings.DATABASES, que a su vez sale de
atlas-credentials.env. El script nunca puede apuntar a otra base que la
que usa la aplicacion.
"""

import argparse
import os
import sys
from pathlib import Path

import django
import pymongo
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / 'atlas-credentials.env')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_projectAFM.settings')
django.setup()

from django.conf import settings  # noqa: E402  requiere django.setup() previo

PALABRA_CONFIRMACION = 'BORRAR'


def datos_de_conexion():
    """Devuelve (uri, nombre_base, opciones) de la base 'default' del proyecto."""
    configuracion = settings.DATABASES['default']
    uri = configuracion.get('HOST')
    nombre_base = configuracion.get('NAME')
    opciones = configuracion.get('OPTIONS') or {}

    if not uri:
        sys.exit('MONGODB_URI vacio: revisa atlas-credentials.env.')
    if not nombre_base:
        sys.exit('MONGODB_DB_NAME vacio: revisa atlas-credentials.env.')

    return uri, nombre_base, opciones


def confirmar(nombre_base, accion):
    """Doble llave humana: sin la palabra exacta no se borra nada."""
    print(f'Base de datos : {nombre_base}')
    print(f'Accion        : {accion}')
    respuesta = input(f'Escribe {PALABRA_CONFIRMACION} para continuar: ')
    return respuesta.strip() == PALABRA_CONFIRMACION


def vaciar_colecciones(base):
    """Borra los documentos de cada coleccion conservando indices y esquema."""
    resumen = []
    for nombre_coleccion in sorted(base.list_collection_names()):
        eliminados = base[nombre_coleccion].delete_many({}).deleted_count
        resumen.append((nombre_coleccion, eliminados))
    return resumen


def main():
    analizador = argparse.ArgumentParser(
        description='Vacia la base de datos de desarrollo (solo para depuracion).',
    )
    analizador.add_argument(
        '--drop',
        action='store_true',
        help='elimina la base completa en vez de vaciar las colecciones',
    )
    analizador.add_argument(
        '--si',
        action='store_true',
        help='omite la confirmacion interactiva',
    )
    argumentos = analizador.parse_args()

    uri, nombre_base, opciones = datos_de_conexion()
    accion = (
        'DROP DATABASE (se pierde tambien el esquema y los indices)'
        if argumentos.drop
        else 'VACIAR COLECCIONES (se conserva el esquema y los indices)'
    )

    if not argumentos.si and not confirmar(nombre_base, accion):
        print('Cancelado: no se toco nada.')
        return 0

    cliente = pymongo.MongoClient(uri, **opciones)
    try:
        if argumentos.drop:
            cliente.drop_database(nombre_base)
            print(f'Base eliminada: {nombre_base}')
            print('Siguiente paso: python manage.py migrate')
            return 0

        resumen = vaciar_colecciones(cliente[nombre_base])
        if not resumen:
            print(f'La base {nombre_base} no tiene colecciones.')
        for nombre_coleccion, eliminados in resumen:
            print(f'  {nombre_coleccion:<32} {eliminados:>6} documentos eliminados')
        print('Colecciones vaciadas. El esquema y los indices siguen intactos.')
    finally:
        cliente.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
