"""Tests for the reviews app: the Review model, its form and moderation flow."""
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from catalog.tests import make_wine
from reviews.forms import ReviewForm
from reviews.models import Review

VALID_REVIEW = {
    'rating': 5,
    'title': 'Excellent wine',
    'comment': 'Really enjoyed this bottle, would buy again.',
}


class ReviewModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw12345678')
        self.wine = make_wine()

    def test_reviews_start_unapproved(self):
        review = Review.objects.create(user=self.user, wine=self.wine, **VALID_REVIEW)

        self.assertFalse(review.is_approved)

    def test_str_representation(self):
        review = Review.objects.create(user=self.user, wine=self.wine, **VALID_REVIEW)

        self.assertEqual(str(review), 'Review by alice for Chateau Test (5★)')

    def test_a_user_can_review_a_wine_only_once(self):
        Review.objects.create(user=self.user, wine=self.wine, **VALID_REVIEW)

        with self.assertRaises(IntegrityError):
            Review.objects.create(user=self.user, wine=self.wine, **VALID_REVIEW)

    def test_different_users_can_review_the_same_wine(self):
        bob = User.objects.create_user(username='bob', password='pw12345678')
        Review.objects.create(user=self.user, wine=self.wine, **VALID_REVIEW)
        Review.objects.create(user=bob, wine=self.wine, **VALID_REVIEW)

        self.assertEqual(self.wine.reviews.count(), 2)

    def test_newest_review_comes_first(self):
        bob = User.objects.create_user(username='bob', password='pw12345678')
        first = Review.objects.create(user=self.user, wine=self.wine, **VALID_REVIEW)
        second = Review.objects.create(user=bob, wine=self.wine, **VALID_REVIEW)

        self.assertEqual(list(Review.objects.all()), [second, first])

    def test_deleting_the_wine_deletes_its_reviews(self):
        Review.objects.create(user=self.user, wine=self.wine, **VALID_REVIEW)

        self.wine.delete()

        self.assertEqual(Review.objects.count(), 0)


class ReviewFormTests(TestCase):
    def test_valid_data_is_accepted(self):
        self.assertTrue(ReviewForm(data=VALID_REVIEW).is_valid())

    def test_short_comment_is_rejected(self):
        form = ReviewForm(data=dict(VALID_REVIEW, comment='Too short'))

        self.assertFalse(form.is_valid())
        self.assertIn('comment', form.errors)

    def test_overlong_comment_is_rejected(self):
        form = ReviewForm(data=dict(VALID_REVIEW, comment='x' * 1001))

        self.assertFalse(form.is_valid())
        self.assertIn('comment', form.errors)

    def test_short_title_is_rejected(self):
        form = ReviewForm(data=dict(VALID_REVIEW, title='Hi'))

        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_rating_above_five_is_rejected(self):
        self.assertFalse(ReviewForm(data=dict(VALID_REVIEW, rating=6)).is_valid())

    def test_rating_below_one_is_rejected(self):
        self.assertFalse(ReviewForm(data=dict(VALID_REVIEW, rating=0)).is_valid())


class AddReviewViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pw12345678')
        self.wine = make_wine()
        self.url = reverse('reviews:add_review', kwargs={'slug': self.wine.slug})

    def test_login_is_required(self):
        response = self.client.post(self.url, VALID_REVIEW)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.count(), 0)

    def test_get_request_is_rejected(self):
        self.client.login(username='alice', password='pw12345678')

        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_review_is_created_and_attached_to_the_user_and_wine(self):
        self.client.login(username='alice', password='pw12345678')

        response = self.client.post(self.url, VALID_REVIEW)

        review = Review.objects.get()
        self.assertRedirects(
            response,
            reverse('catalog:wine_detail', kwargs={'slug': self.wine.slug}),
        )
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.wine, self.wine)
        self.assertFalse(review.is_approved)

    def test_second_review_from_the_same_user_is_blocked(self):
        self.client.login(username='alice', password='pw12345678')
        self.client.post(self.url, VALID_REVIEW)

        self.client.post(self.url, dict(VALID_REVIEW, title='Another go'))

        self.assertEqual(Review.objects.count(), 1)

    def test_invalid_data_creates_nothing(self):
        self.client.login(username='alice', password='pw12345678')

        self.client.post(self.url, dict(VALID_REVIEW, comment='short'))

        self.assertEqual(Review.objects.count(), 0)

    def test_review_for_an_inactive_wine_returns_404(self):
        hidden = make_wine(name='Hidden', is_active=False)
        self.client.login(username='alice', password='pw12345678')

        response = self.client.post(
            reverse('reviews:add_review', kwargs={'slug': hidden.slug}),
            VALID_REVIEW,
        )

        self.assertEqual(response.status_code, 404)
