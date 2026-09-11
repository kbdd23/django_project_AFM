"""nuke.py - Deja la base de datos de desarrollo en cero.

No es parte del flujo de la aplicacion: existe para depurar cuando los
datos de prueba estorban (mesas duplicadas, reservas de prueba encadenadas,
usuarios basura, etc).

Uso:
    python nuke.py          vacia las colecciones de la aplicacion
    python nuke.py --drop   elimina la base completa (hay que migrar de nuevo)
    python nuke.py --si     omite la confirmacion interactiva

Nunca toca las colecciones de estado de Django (django_migrations,
django_content_type, auth_permission): borrarlas deja el esquema creado
pero sin registro de las migraciones aplicadas, y el siguiente 'migrate'
intenta recrear colecciones que ya existen.

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


COLECCIONES_PROTEGIDAS = {
    'django_migrations',    # registro de migraciones aplicadas: sin el, Django cree que la base esta vacia
    'django_content_type',  # catalogo de modelos: lo consume el sistema de permisos
    'auth_permission',      # permisos por modelo: los reconstruye migrate, pero no son datos de prueba
}


def vaciar_colecciones(base):
    """Borra los documentos de cada coleccion conservando indices, esquema y estado de Django.

    Devuelve (vaciadas, protegidas). Las protegidas sostienen el estado interno de Django:
    si se borran, el esquema queda creado pero sin registro de que las migraciones corrieron,
    y el siguiente 'migrate' intenta recrear colecciones que ya existen.
    """
    vaciadas = []
    protegidas = []
    for nombre_coleccion in sorted(base.list_collection_names()):
        if nombre_coleccion in COLECCIONES_PROTEGIDAS:
            protegidas.append(nombre_coleccion)
            continue
        eliminados = base[nombre_coleccion].delete_many({}).deleted_count
        vaciadas.append((nombre_coleccion, eliminados))
    return vaciadas, protegidas


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

        vaciadas, protegidas = vaciar_colecciones(cliente[nombre_base])
        if not vaciadas and not protegidas:
            print(f'La base {nombre_base} no tiene colecciones.')
        for nombre_coleccion, eliminados in vaciadas:
            print(f'  {nombre_coleccion:<32} {eliminados:>6} documentos eliminados')
        for nombre_coleccion in protegidas:
            print(f'  {nombre_coleccion:<32} protegida (estado de Django)')
        print('Colecciones vaciadas. El esquema y los indices siguen intactos.')
    finally:
        cliente.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
