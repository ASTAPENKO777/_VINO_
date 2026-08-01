"""Tests for the accounts app: profile signals, registration, login and profile edit."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.forms import UserProfileForm, UserRegistrationForm
from accounts.models import UserProfile

REGISTRATION_DATA = {
    'username': 'alice2000',
    'email': 'alice@example.com',
    'password1': 'Str0ngPassw0rd!',
    'password2': 'Str0ngPassw0rd!',
}


class UserProfileSignalTests(TestCase):
    def test_a_profile_is_created_for_every_new_user(self):
        user = User.objects.create_user(username='alice', password='pw12345678')

        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_saving_a_user_does_not_create_a_second_profile(self):
        user = User.objects.create_user(username='alice', password='pw12345678')

        user.first_name = 'Alice'
        user.save()

        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)

    def test_profile_str(self):
        user = User.objects.create_user(username='alice', password='pw12345678')

        self.assertEqual(str(user.profile), 'Profile of alice')

    def test_deleting_the_user_deletes_the_profile(self):
        user = User.objects.create_user(username='alice', password='pw12345678')

        user.delete()

        self.assertEqual(UserProfile.objects.count(), 0)


class RegistrationFormTests(TestCase):
    def test_valid_data_is_accepted(self):
        self.assertTrue(UserRegistrationForm(data=REGISTRATION_DATA).is_valid())

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username='existing', email='alice@example.com', password='pw12345678'
        )

        form = UserRegistrationForm(data=REGISTRATION_DATA)

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_non_alphanumeric_username_is_rejected(self):
        form = UserRegistrationForm(data=dict(REGISTRATION_DATA, username='al_ice'))

        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_mismatched_passwords_are_rejected(self):
        form = UserRegistrationForm(
            data=dict(REGISTRATION_DATA, password2='SomethingElse!1')
        )

        self.assertFalse(form.is_valid())

    def test_email_is_required(self):
        form = UserRegistrationForm(data=dict(REGISTRATION_DATA, email=''))

        self.assertFalse(form.is_valid())


class RegistrationViewTests(TestCase):
    def setUp(self):
        self.url = reverse('accounts:register')

    def test_page_renders(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_successful_registration_creates_and_logs_in_the_user(self):
        response = self.client.post(self.url, REGISTRATION_DATA)

        self.assertRedirects(response, reverse('catalog:wine_list'))
        self.assertTrue(User.objects.filter(username='alice2000').exists())
        self.assertIn('_auth_user_id', self.client.session)

    def test_invalid_registration_creates_nothing(self):
        self.client.post(self.url, dict(REGISTRATION_DATA, password2='mismatch'))

        self.assertEqual(User.objects.count(), 0)

    def test_logged_in_user_is_redirected_away(self):
        User.objects.create_user(username='alice', password='pw12345678')
        self.client.login(username='alice', password='pw12345678')

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('catalog:wine_list'))


class LoginLogoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw12345678')
        self.url = reverse('accounts:login')

    def test_page_renders(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_correct_credentials_log_the_user_in(self):
        response = self.client.post(
            self.url, {'username': 'alice', 'password': 'pw12345678'}
        )

        self.assertRedirects(response, reverse('catalog:wine_list'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_wrong_password_does_not_log_in(self):
        self.client.post(self.url, {'username': 'alice', 'password': 'wrong'})

        self.assertNotIn('_auth_user_id', self.client.session)

    def test_unknown_user_does_not_log_in(self):
        self.client.post(self.url, {'username': 'nobody', 'password': 'pw12345678'})

        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_clears_the_session(self):
        self.client.login(username='alice', password='pw12345678')

        self.client.get(reverse('accounts:logout'))

        self.assertNotIn('_auth_user_id', self.client.session)


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw12345678')
        self.url = reverse('accounts:profile')

    def test_login_is_required(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_page_renders_for_a_logged_in_user(self):
        self.client.login(username='alice', password='pw12345678')

        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_profile_can_be_updated(self):
        self.client.login(username='alice', password='pw12345678')

        self.client.post(
            self.url,
            {
                'phone_number': '+380501234567',
                'address': 'вул. Хрещатик, 1',
                'city': 'Київ',
                'country': 'Україна',
                'postal_code': '01001',
            },
        )
        self.user.profile.refresh_from_db()

        self.assertEqual(self.user.profile.city, 'Київ')


class UserProfileFormTests(TestCase):
    def test_letters_in_the_phone_number_are_rejected(self):
        form = UserProfileForm(data={'phone_number': 'not-a-phone'})

        self.assertFalse(form.is_valid())
        self.assertIn('phone_number', form.errors)

    def test_plus_and_dashes_are_allowed(self):
        self.assertTrue(UserProfileForm(data={'phone_number': '+380-50-1234567'}).is_valid())

    def test_phone_number_is_optional(self):
        self.assertTrue(UserProfileForm(data={}).is_valid())
