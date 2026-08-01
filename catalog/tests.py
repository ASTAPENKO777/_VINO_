"""Tests for the catalog app: Wine model behaviour and the public views."""
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from catalog.models import Country, Wine, WineType
from reviews.models import Review


def make_wine(**overrides):
    """Create a Wine with sensible defaults, overridable per test."""
    wine_type = overrides.pop('wine_type', None) or WineType.objects.get_or_create(
        name='Red'
    )[0]
    country = overrides.pop('country', None) or Country.objects.get_or_create(
        name='France', defaults={'code': 'FRA'}
    )[0]
    fields = {
        'name': 'Chateau Test',
        'description': 'A test wine.',
        'price': Decimal('250.00'),
        'year': 2020,
        'stock_quantity': 10,
        'wine_type': wine_type,
        'country': country,
    }
    fields.update(overrides)
    return Wine.objects.create(**fields)


class WineModelTests(TestCase):
    def test_slug_is_generated_from_name_and_year(self):
        wine = make_wine(name='Chateau Margaux', year=2015)

        self.assertEqual(wine.slug, 'chateau-margaux-2015')

    def test_explicit_slug_is_not_overwritten(self):
        wine = make_wine(slug='custom-slug')

        wine.name = 'Renamed'
        wine.save()

        self.assertEqual(wine.slug, 'custom-slug')

    def test_str_includes_name_and_year(self):
        wine = make_wine(name='Barolo', year=2018)

        self.assertEqual(str(wine), 'Barolo (2018)')

    def test_get_absolute_url_points_at_the_detail_view(self):
        wine = make_wine()

        self.assertEqual(
            wine.get_absolute_url(),
            reverse('catalog:wine_detail', kwargs={'slug': wine.slug}),
        )

    def test_in_stock_reflects_stock_quantity(self):
        self.assertTrue(make_wine(name='A', stock_quantity=1).in_stock)
        self.assertFalse(make_wine(name='B', stock_quantity=0).in_stock)

    def test_default_ordering_is_newest_first(self):
        first = make_wine(name='First')
        second = make_wine(name='Second')

        self.assertEqual(list(Wine.objects.all()), [second, first])


class AverageRatingTests(TestCase):
    def setUp(self):
        self.wine = make_wine()

    def _review(self, username, rating, approved):
        user = User.objects.create_user(username=username, password='pw12345678')
        return Review.objects.create(
            user=user,
            wine=self.wine,
            rating=rating,
            title='A title',
            comment='A sufficiently long comment.',
            is_approved=approved,
        )

    def test_is_none_without_any_review(self):
        self.assertIsNone(self.wine.average_rating)

    def test_is_none_when_no_review_is_approved(self):
        self._review('u1', 5, approved=False)

        self.assertIsNone(self.wine.average_rating)

    def test_averages_only_approved_reviews(self):
        self._review('u1', 5, approved=True)
        self._review('u2', 3, approved=True)
        self._review('u3', 1, approved=False)  # must be ignored

        self.assertEqual(self.wine.average_rating, 4.0)


class WineListViewTests(TestCase):
    def setUp(self):
        self.red = WineType.objects.create(name='Red')
        self.white = WineType.objects.create(name='White')
        self.france = Country.objects.create(name='France', code='FRA')
        self.italy = Country.objects.create(name='Italy', code='ITA')

        self.cheap = make_wine(
            name='Cheap', price=Decimal('100'), year=2019,
            wine_type=self.red, country=self.france,
        )
        self.pricey = make_wine(
            name='Pricey', price=Decimal('900'), year=2021,
            wine_type=self.white, country=self.italy,
        )
        self.hidden = make_wine(
            name='Hidden', is_active=False,
            wine_type=self.red, country=self.france,
        )
        self.url = reverse('catalog:wine_list')

    def test_inactive_wines_are_hidden(self):
        names = [w.name for w in self.client.get(self.url).context['wines']]

        self.assertIn('Cheap', names)
        self.assertNotIn('Hidden', names)

    def test_filter_by_wine_type(self):
        response = self.client.get(self.url, {'wine_type': self.white.id})

        self.assertEqual([w.name for w in response.context['wines']], ['Pricey'])

    def test_filter_by_country(self):
        response = self.client.get(self.url, {'country': self.italy.id})

        self.assertEqual([w.name for w in response.context['wines']], ['Pricey'])

    def test_sort_by_price_ascending(self):
        response = self.client.get(self.url, {'sort': 'price_asc'})

        self.assertEqual(
            [w.name for w in response.context['wines']], ['Cheap', 'Pricey']
        )

    def test_sort_by_price_descending(self):
        response = self.client.get(self.url, {'sort': 'price_desc'})

        self.assertEqual(
            [w.name for w in response.context['wines']], ['Pricey', 'Cheap']
        )

    def test_unknown_sort_value_is_ignored(self):
        response = self.client.get(self.url, {'sort': 'nonsense'})

        self.assertEqual(response.status_code, 200)

    def test_context_counters_exclude_inactive_wines(self):
        context = self.client.get(self.url).context

        self.assertEqual(context['total_wines'], 2)
        self.assertEqual(context['total_countries'], 2)
        self.assertEqual(context['total_types'], 2)


class WineDetailViewTests(TestCase):
    def setUp(self):
        self.wine = make_wine()
        self.user = User.objects.create_user(username='alice', password='pw12345678')
        self.url = reverse('catalog:wine_detail', kwargs={'slug': self.wine.slug})

    def test_unknown_slug_returns_404(self):
        response = self.client.get(
            reverse('catalog:wine_detail', kwargs={'slug': 'nope'})
        )

        self.assertEqual(response.status_code, 404)

    def test_only_approved_reviews_are_shown(self):
        other = User.objects.create_user(username='bob', password='pw12345678')
        Review.objects.create(
            user=self.user, wine=self.wine, rating=5,
            title='Great', comment='Long enough comment.', is_approved=True,
        )
        Review.objects.create(
            user=other, wine=self.wine, rating=1,
            title='Awful', comment='Long enough comment.', is_approved=False,
        )

        reviews = self.client.get(self.url).context['reviews']

        self.assertEqual([r.title for r in reviews], ['Great'])

    def test_user_has_review_flag_is_absent_for_anonymous_visitors(self):
        self.assertNotIn('user_has_review', self.client.get(self.url).context)

    def test_user_has_review_flag_tracks_the_logged_in_user(self):
        self.client.login(username='alice', password='pw12345678')

        self.assertFalse(self.client.get(self.url).context['user_has_review'])

        Review.objects.create(
            user=self.user, wine=self.wine, rating=4,
            title='Nice', comment='Long enough comment.',
        )

        self.assertTrue(self.client.get(self.url).context['user_has_review'])


class DeleteWineTests(TestCase):
    def setUp(self):
        self.wine = make_wine()
        self.url = reverse('catalog:wine_delete', kwargs={'slug': self.wine.slug})

    def test_anonymous_visitor_cannot_delete(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Wine.objects.filter(pk=self.wine.pk).exists())

    def test_regular_user_cannot_delete(self):
        User.objects.create_user(username='alice', password='pw12345678')
        self.client.login(username='alice', password='pw12345678')

        self.client.post(self.url)

        self.assertTrue(Wine.objects.filter(pk=self.wine.pk).exists())

    def test_staff_can_delete(self):
        User.objects.create_user(
            username='admin', password='pw12345678', is_staff=True
        )
        self.client.login(username='admin', password='pw12345678')

        response = self.client.post(self.url)

        self.assertRedirects(response, reverse('catalog:wine_list'))
        self.assertFalse(Wine.objects.filter(pk=self.wine.pk).exists())

    def test_get_request_is_rejected(self):
        User.objects.create_user(
            username='admin', password='pw12345678', is_staff=True
        )
        self.client.login(username='admin', password='pw12345678')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Wine.objects.filter(pk=self.wine.pk).exists())


class StaticPageTests(TestCase):
    def test_about_page(self):
        self.assertEqual(self.client.get(reverse('catalog:about')).status_code, 200)

    def test_contacts_page(self):
        self.assertEqual(
            self.client.get(reverse('catalog:contacts')).status_code, 200
        )
