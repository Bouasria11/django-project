from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Genre, Film, Review, Watchlist

# Workaround for Python 3.14 compatibility with Django test framework
# Patch Context.__copy__ to avoid 'super' object has no attribute 'dicts' error
try:
    from django.template.context import Context, RequestContext

    def _patched_context_copy(self):
        # Create a new context of the same type
        if isinstance(self, RequestContext):
            new = RequestContext(self.request, {})
        else:
            new = Context({})
        # Copy state
        new.dicts = self.dicts[:]
        new.autoescape = self.autoescape
        new.use_l10n = getattr(self, 'use_l10n', True)
        new.use_tz = getattr(self, 'use_tz', True)
        return new

    Context.__copy__ = _patched_context_copy
except Exception:
    pass

User = get_user_model()

class ModelTests(TestCase):
    def setUp(self):
        self.spectator = User.objects.create_user(
            username='spectator1',
            email='spec@test.com',
            password='testpass123',
            role=User.Role.SPECTATOR
        )
        self.admin = User.objects.create_user(
            username='admin1',
            email='admin@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.genre = Genre.objects.create(name='Action')
        self.film = Film.objects.create(
            title='Test Film',
            genre=self.genre,
            description='Test description',
            release_date='2024-01-01'
        )

    def test_user_creation(self):
        self.assertEqual(self.spectator.username, 'spectator1')
        self.assertEqual(self.spectator.role, User.Role.SPECTATOR)
        self.assertFalse(self.spectator.is_admin_role)
        self.assertTrue(self.spectator.is_spectator)

    def test_admin_creation(self):
        self.assertEqual(self.admin.role, User.Role.ADMIN)
        self.assertTrue(self.admin.is_admin_role)
        self.assertTrue(self.admin.is_staff)
        self.assertTrue(self.admin.is_superuser)

    def test_film_creation(self):
        self.assertEqual(self.film.title, 'Test Film')
        self.assertEqual(self.film.genre, self.genre)
        self.assertIsNone(self.film.average_rating)

    def test_review_creation(self):
        review = Review.objects.create(
            user=self.spectator,
            film=self.film,
            rating=5,
            comment='Excellent!'
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(self.film.average_rating, 5.0)
        self.assertEqual(self.film.review_count, 1)

    def test_watchlist_creation(self):
        watchlist_item = Watchlist.objects.create(
            user=self.spectator,
            film=self.film
        )
        self.assertTrue(Watchlist.objects.filter(user=self.spectator, film=self.film).exists())

    def test_unique_review_constraint(self):
        Review.objects.create(user=self.spectator, film=self.film, rating=5)
        with self.assertRaises(Exception):
            Review.objects.create(user=self.spectator, film=self.film, rating=4)

    def test_genre_str(self):
        self.assertEqual(str(self.genre), 'Action')

    def test_film_str(self):
        self.assertEqual(str(self.film), 'Test Film')

class ViewTests(TestCase):
    def setUp(self):
        self.spectator = User.objects.create_user(
            username='spectator1',
            email='spec@test.com',
            password='testpass123',
            role=User.Role.SPECTATOR
        )
        self.admin = User.objects.create_user(
            username='admin1',
            email='admin@test.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.genre = Genre.objects.create(name='Comedy')
        self.film = Film.objects.create(
            title='Comedy Film',
            genre=self.genre,
            description='Funny movie',
            release_date='2024-01-01'
        )

    def test_home_view(self):
        response = self.client.get(reverse('movies:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'movies/home.html')

    def test_film_list_view(self):
        response = self.client.get(reverse('movies:film_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'movies/film_list.html')
        self.assertIn('page_obj', response.context)

    def test_film_detail_view(self):
        response = self.client.get(reverse('movies:film_detail', kwargs={'pk': self.film.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'movies/film_detail.html')
        self.assertEqual(response.context['film'], self.film)

    def test_search_view(self):
        response = self.client.get(reverse('movies:search_films'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'movies/search.html')

    def test_login_required_views(self):
        # Test that add_review requires login
        response = self.client.get(reverse('movies:add_review', kwargs={'pk': self.film.pk}))
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Test that user_dashboard requires login
        response = self.client.get(reverse('movies:user_dashboard'))
        self.assertEqual(response.status_code, 302)

        # Test that recommendations requires login
        response = self.client.get(reverse('movies:recommendations'))
        self.assertEqual(response.status_code, 302)

    def test_admin_required_views(self):
        # Test film_create requires admin
        self.client.login(username='spectator1', password='testpass123')
        response = self.client.get(reverse('movies:film_create'))
        self.assertEqual(response.status_code, 302)  # Redirect

        self.client.login(username='admin1', password='testpass123')
        response = self.client.get(reverse('movies:film_create'))
        self.assertEqual(response.status_code, 200)

    def test_film_crud_operations(self):
        self.client.login(username='admin1', password='testpass123')

        # Test create
        response = self.client.post(reverse('movies:film_create'), {
            'title': 'New Film',
            'genre': self.genre.id,
            'description': 'New description',
            'release_date': '2024-02-02',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        new_film = Film.objects.get(title='New Film')
        self.assertIsNotNone(new_film)

        # Test update
        response = self.client.post(reverse('movies:film_update', kwargs={'pk': new_film.pk}), {
            'title': 'Updated Film',
            'genre': self.genre.id,
            'description': 'Updated description',
            'release_date': '2024-03-03',
        })
        new_film.refresh_from_db()
        self.assertEqual(new_film.title, 'Updated Film')

        # Test delete
        response = self.client.post(reverse('movies:film_delete', kwargs={'pk': new_film.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Film.objects.filter(pk=new_film.pk).exists())

    def test_review_flow(self):
        self.client.login(username='spectator1', password='testpass123')

        # Add review
        response = self.client.post(reverse('movies:add_review', kwargs={'pk': self.film.pk}), {
            'rating': 4,
            'comment': 'Great movie!'
        })
        self.assertEqual(response.status_code, 302)
        review = Review.objects.get(user=self.spectator, film=self.film)
        self.assertEqual(review.rating, 4)

        # Update review
        response = self.client.post(reverse('movies:add_review', kwargs={'pk': self.film.pk}), {
            'rating': 5,
            'comment': 'Even better!'
        })
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)

        # Delete review
        response = self.client.get(reverse('movies:delete_review', kwargs={'pk': self.film.pk, 'review_id': review.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())

    def test_watchlist_toggle(self):
        self.client.login(username='spectator1', password='testpass123')

        # Add to watchlist
        response = self.client.get(reverse('movies:toggle_watchlist', kwargs={'pk': self.film.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Watchlist.objects.filter(user=self.spectator, film=self.film).exists())

        # Remove from watchlist
        response = self.client.get(reverse('movies:toggle_watchlist', kwargs={'pk': self.film.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Watchlist.objects.filter(user=self.spectator, film=self.film).exists())

class AuthenticationTests(TestCase):
    def test_register_view(self):
        response = self.client.get(reverse('movies:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'movies/register.html')

        response = self.client.post(reverse('movies:register'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login_logout(self):
        User.objects.create_user(username='testuser', email='test@test.com', password='testpass123')

        # Test login
        response = self.client.post(reverse('movies:login'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)

        # Test logout
        response = self.client.get(reverse('movies:logout'))
        self.assertEqual(response.status_code, 302)

class SearchTests(TestCase):
    def setUp(self):
        self.genre1 = Genre.objects.create(name='Action')
        self.genre2 = Genre.objects.create(name='Comedy')
        self.film1 = Film.objects.create(
            title='Action Movie',
            genre=self.genre1,
            description='Exciting action film',
            release_date='2024-01-01'
        )
        self.film2 = Film.objects.create(
            title='Comedy Show',
            genre=self.genre2,
            description='Funny comedy',
            release_date='2023-01-01'
        )

    def test_search_by_title(self):
        response = self.client.get(reverse('movies:search_films') + '?q=Action')
        self.assertContains(response, 'Action Movie')
        self.assertNotContains(response, 'Comedy Show')

    def test_search_by_genre(self):
        response = self.client.get(reverse('movies:search_films') + '?genre=' + str(self.genre2.id))
        self.assertContains(response, 'Comedy Show')
        self.assertNotContains(response, 'Action Movie')

    def test_search_by_year(self):
        response = self.client.get(reverse('movies:search_films') + '?year=2024')
        self.assertContains(response, 'Action Movie')
        self.assertNotContains(response, 'Comedy Show')

    def test_combined_search(self):
        response = self.client.get(reverse('movies:search_films') + '?q=Comedy&genre=' + str(self.genre2.id))
        self.assertContains(response, 'Comedy Show')
