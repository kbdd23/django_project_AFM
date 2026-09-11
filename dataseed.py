#Script de insercion de datos de prueba.
#Define 11 usuarios cliente y 3 usuarios meseros. Adicionalmente se define una
#lista con 4 administradores para futuras implementaciones.
#
#Uso (desde la carpeta donde vive manage.py):
#    ./.venv/bin/python manage.py shell < dataseed.py
#
#Todas las funciones son idempotentes: si el correo ya existe, se salta.
#El username es el correo, igual que en signup_view: asi el login por email
#funciona con los mismos datos.

from pages.models import User

CLIENTES = [
    ('Fernando Reveco', 'profesor.reveco@gmail.com', '1234'),
    ('Ana García', 'ana.garcia@gmail.com', '1234'),
    ('Luis Lazo', 'luis.lazo@gmail.com', '1234'),
    ('Rodrigo Pradenas', 'rodrigo.pradenas@gmail.com', '1234'),
    ('Gonzalo Rojas', 'gonza.rojas@gmail.com', '1234'),
    ('Lucía Cuevas', 'lucy.cave@gmail.com', '1234'),
    ('Marianne Raine', 'mary.raine@gmail.com', '1234'),
    ('Ziora Deen', 'zora.dee@gmail.com', '1234'),
    ('Lexis Null', 'lexnull@gmail.com', '1234'),
    ('Kevin Wayne', 'kevin.wayne@gmail.com', '1234'),
    ('Usuario', 'usuario@gmail.com', '1234'),
]

MESEROS = [
    ('Ana Barrientos', 'ana@abaroa.com', '1234'),
    ('Francisco Vera', 'goated@abaroa.com', '1234'),
    ('Matías Cáceres', 'matias@abaroa.com', '1234'),
]

ADMINISTRADORES = [
    ('Ana Barrientos', 'ana@abaroa.cl', '1234'),
    ('Francisco Vera', 'fran@abaroa.cl', '1234'),
    ('Matías Cáceres', 'matias@abaroa.cl', '1234'),
    ('Administrador', 'admin@abaroal.cl', '1234'),
]


def crear_clientes():
    """Alta de clientes. create_user impone el rol cliente por defecto."""
    creados = 0
    for nombre, correo, clave in CLIENTES:
        if User.objects.filter(username=correo).exists():
            continue
        User.objects.create_user(
            username=correo,
            email=correo,
            password=clave,
            first_name=nombre,
        )
        creados += 1
    return creados


def crear_meseros():
    """Alta de meseros.

    Usa crear_mesero() y no create_user(): el manager rechaza el parametro
    'rol' a proposito, asi que el rol se asigna despues de crear el usuario.
    """
    creados = 0
    for nombre, correo, clave in MESEROS:
        if User.objects.filter(username=correo).exists():
            continue
        User.crear_mesero(
            username=correo,
            email=correo,
            password=clave,
            first_name=nombre,
        )
        creados += 1
    return creados


def poblar():
    """Corre las tres cargas y reporta cuantos usuarios nuevos entraron."""
    print('clientes nuevos:', crear_clientes())
    print('meseros nuevos:', crear_meseros())
    print('total de usuarios:', User.objects.count())


if __name__ == '__main__':
    poblar()
