from django.test import TestCase, Client
from django.urls import reverse
from .models import User


class SignupTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')

    def test_signup_crea_usuario_con_telefono(self):
        response = self.client.post(self.signup_url, {
            'nombre': 'Francisco Vera',
            'email': 'fran@test.cl',
            'telefono': '+56 9 1234 5678',
            'password': 'clave-segura-123',
            'password2': 'clave-segura-123',
        })

        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(username='fran@test.cl')
        self.assertEqual(user.email, 'fran@test.cl')
        self.assertEqual(user.first_name, 'Francisco Vera')
        self.assertEqual(user.telefono, '+56 9 1234 5678')
        self.assertTrue(user.check_password('clave-segura-123'))

    def test_signup_con_passwords_distintas_no_crea_usuario(self):
        response = self.client.post(self.signup_url, {
            'nombre': 'Francisco Vera',
            'email': 'fran@test.cl',
            'telefono': '',
            'password': 'clave-uno',
            'password2': 'clave-dos',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Las contraseñas no coinciden.')
        self.assertFalse(User.objects.filter(username='fran@test.cl').exists())

    def test_signup_con_email_repetido_no_crea_duplicado(self):
        User.objects.create_user(username='fran@test.cl', email='fran@test.cl', password='clave-123')

        response = self.client.post(self.signup_url, {
            'nombre': 'Otro Fran',
            'email': 'fran@test.cl',
            'telefono': '',
            'password': 'clave-456',
            'password2': 'clave-456',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ya existe una cuenta con ese correo.')
        self.assertEqual(User.objects.filter(username='fran@test.cl').count(), 1)


class LoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.home_url = reverse('home')
        self.user = User.objects.create_user(
            username='fran@test.cl',
            email='fran@test.cl',
            password='clave-segura-123',
            first_name='Francisco',
        )

    def test_login_valido_redirige_al_inicio_y_autentica(self):
        response = self.client.post(self.login_url, {
            'email': 'fran@test.cl',
            'password': 'clave-segura-123',
        })

        self.assertRedirects(response, self.home_url)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_invalido_muestra_error(self):
        response = self.client.post(self.login_url, {
            'email': 'fran@test.cl',
            'password': 'clave-incorrecta',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Usuario o contraseña incorrectos.')


class HomeAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.home_url = reverse('home')

    def test_inicio_sin_sesion_muestra_boton_reservar(self):
        response = self.client.get(self.home_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'btn-reservar-gigante')
        self.assertContains(response, 'Reservar')
        self.assertNotContains(response, 'Estás logeado')

    def test_inicio_con_sesion_muestra_estado_logeado(self):
        User.objects.create_user(
            username='fran@test.cl',
            email='fran@test.cl',
            password='clave-segura-123',
            first_name='Francisco',
        )
        self.client.login(username='fran@test.cl', password='clave-segura-123')

        response = self.client.get(self.home_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Estás logeado')
        self.assertContains(response, 'Francisco')
        self.assertNotContains(response, 'btn-reservar-gigante')

    def test_logout_desautentica(self):
        User.objects.create_user(
            username='fran@test.cl',
            email='fran@test.cl',
            password='clave-segura-123',
        )
        self.client.login(username='fran@test.cl', password='clave-segura-123')

        response = self.client.get(reverse('logout'))

        self.assertRedirects(response, self.home_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
