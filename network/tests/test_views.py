"""Test views module functions."""

import json

from django.test import Client, TestCase
from django.urls import reverse

from network.models import Post, User


class ComposeViewTest(TestCase):
    """Tests for the compose method."""

    def setUp(self):
        """Setting up for compose tests."""
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client = Client()

    def test_compose_empty_text(self):
        """Test that composing an empty post generates an error (400)."""
        self.client.login(username="testuser", password="pass")
        response = self.client.post(
            reverse("compose"),
            content_type="application/json",
            data=json.dumps({"text": "   "}),
        )
        self.assertEqual(response.status_code, 400)

    def test_compose_invalid_json(self):
        """Test that compose with invalid json generates an error (400)."""
        self.client.login(username="testuser", password="pass")
        response = self.client.post(
            reverse("compose"), content_type="application/json", data="not-json"
        )
        self.assertEqual(response.status_code, 400)

    def test_compose_missing_json(self):
        """Test that compose with missing json generates an error (400)."""
        self.client.login(username="testuser", password="pass")
        response = self.client.post(reverse("compose"), content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_compose_requires_login(self):
        """Test that composing without logging in generates an error (302)."""
        response = self.client.put(
            reverse("compose"),
            content_type="application/json",
            data=json.dumps({"text": "Anonymous post"}),
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_compose_success(self):
        """Test that composing is successful."""
        self.client.login(username="testuser", password="pass")
        response = self.client.post(
            reverse("compose"),
            content_type="application/json",
            data=json.dumps({"text": "Hello World!"}),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Post.objects.count(), 1)

    def test_compose_wrong_method(self):
        """Test that compose with get method generates an error (400)."""
        self.client.login(username="testuser", password="pass")
        response = self.client.get(reverse("compose"))
        self.assertEqual(response.status_code, 400)


class EditPostViewTest(TestCase):
    """Tests for the edit_post method."""

    def setUp(self):
        """Setting up for edit_post tests."""
        self.client = Client()
        self.author = User.objects.create_user(username="author", password="pass123")
        self.other_user = User.objects.create_user(username="other", password="pass123")
        self.post = Post.objects.create(user=self.author, text="Original text")

    def test_edit_nonexistent_post_returns_404(self):
        """Test for an edit post on a nonexistent post."""
        self.client.login(username="author", password="pass123")
        response = self.client.put(
            reverse("edit_post", args=[9999]),  # Assuming 9999 doesn't exist
            data=json.dumps({"text": "Trying to edit nonexistent post"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_edit_post_by_non_author_forbidden(self):
        """Test that calling edit_post by non author generates an error (400)."""
        self.client.login(username="other", password="pass123")
        response = self.client.put(
            reverse("edit_post", args=[self.post.id]),
            data=json.dumps({"text": "Hacked!"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, "Original text")

    def test_edit_post_requires_login(self):
        """Test that calling edit_post without logging in generates an error (302)."""
        response = self.client.put(
            reverse("edit_post", args=[self.post.id]),
            data=json.dumps({"text": "Anonymous edit"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_edit_post_same_text_does_not_set_was_edited(self):
        """Test that calling edit_post with original text doesn't set was_edited."""
        self.client.login(username="author", password="pass123")
        response = self.client.put(
            reverse("edit_post", args=[self.post.id]),
            data=json.dumps({"text": "Original text"}),  # same as before
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertFalse(self.post.was_edited)

    def test_edit_post_success(self):
        """Test for an edit post by the author."""
        self.client.login(username="author", password="pass123")
        response = self.client.put(
            reverse("edit_post", args=[self.post.id]),
            data=json.dumps({"text": "Updated text"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, "Updated text")
        self.assertTrue(self.post.was_edited)

    def test_edit_post_with_empty_text(self):
        """Test that calling edit_post with empty text generates an error (400)."""
        self.client.login(username="author", password="pass123")
        response = self.client.put(
            reverse("edit_post", args=[self.post.id]),
            data=json.dumps({"text": "   "}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_edit_post_with_invalid_json(self):
        """Test that calling edit_post with invalid json generates an error (400)."""
        self.client.login(username="author", password="pass123")
        response = self.client.put(
            reverse("edit_post", args=[self.post.id]),
            data="not-json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_edit_post_with_missing_json(self):
        """Test that calling edit_post with missing json generates an error (400)."""
        self.client.login(username="author", password="pass123")
        response = self.client.put(
            reverse("edit_post", args=[self.post.id]),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_edit_post_wrong_method(self):
        """Test that calling edit_post with get method generates an error (400)."""
        self.client.login(username="author", password="pass123")
        response = self.client.get(reverse("edit_post", args=[self.post.id]))
        self.assertEqual(response.status_code, 400)


class IndexViewTest(TestCase):
    """Tests for the index view that displays all posts with pagination."""

    def setUp(self):
        """Create a test user and 25 posts for pagination tests."""
        self.client = Client()
        self.user = User.objects.create_user(username="tester", password="pass123")
        for i in range(25):
            Post.objects.create(user=self.user, text=f"Post {i + 1}")

    def test_index_pagination_out_of_range_page(self):
        """Ensure requesting an invalid page number returns the last page."""
        response = self.client.get(reverse("index") + "?page=999")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["page"].has_other_pages())
        self.assertEqual(
            response.context["page"].number,
            response.context["page"].paginator.num_pages,
        )

    def test_index_pagination_page_1(self):
        """Ensure page 1 returns the first 10 posts."""
        response = self.client.get(reverse("index") + "?page=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page"]), 10)

    def test_index_pagination_page_3(self):
        """Ensure page 3 returns the final 5 posts."""
        response = self.client.get(reverse("index") + "?page=3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page"]), 5)

    def test_index_view_anonymous_user(self):
        """Ensure anonymous users can access the index view."""
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "network/index.html")

    def test_index_view_authenticated_user(self):
        """Ensure authenticated users can access the index view."""
        self.client.login(username="tester", password="pass123")
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "network/index.html")


class ProfileViewTest(TestCase):
    """Tests for the profile view that shows a user's posts and follow status."""

    def setUp(self):
        """Create users and posts for testing profile behavior."""
        self.client = Client()
        self.alice = User.objects.create_user(username="alice", password="pass123")
        self.bob = User.objects.create_user(username="bob", password="pass123")
        for i in range(15):
            Post.objects.create(user=self.bob, text=f"Bob's post {i+1}")

    def test_is_following_flag_when_following(self):
        """Ensure `is_following` is True if the logged-in user is following the profile owner."""
        self.alice.following.add(self.bob)
        self.client.login(username="alice", password="pass123")
        response = self.client.get(reverse("profile", args=[self.bob.username]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_following"])

    def test_is_following_flag_when_not_following(self):
        """Ensure `is_following` is False if the logged-in user is not following the profile owner."""
        self.client.login(username="alice", password="pass123")
        response = self.client.get(reverse("profile", args=[self.bob.username]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_following"])

    def test_is_own_profile_flag(self):
        """Ensure `is_own_profile` is True when viewing your own profile."""
        self.client.login(username="alice", password="pass123")
        response = self.client.get(reverse("profile", args=[self.alice.username]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_own_profile"])

    def test_nonexistent_profile_returns_404(self):
        """Ensure requesting a profile that doesn't exist returns 404."""
        response = self.client.get(reverse("profile", args=["ghost"]))
        self.assertEqual(response.status_code, 404)

    def test_pagination_on_profile_posts(self):
        """Ensure profile post pagination splits posts correctly."""
        response = self.client.get(
            reverse("profile", args=[self.bob.username]) + "?page=2"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page"]), 5)

    def test_profile_view_anonymous_user(self):
        """Ensure anonymous users can view profiles."""
        response = self.client.get(reverse("profile", args=[self.bob.username]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("page", response.context)

    def test_profile_view_authenticated_user(self):
        """Ensure authenticated users can view other users' profiles."""
        self.client.login(username="alice", password="pass123")
        response = self.client.get(reverse("profile", args=[self.bob.username]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("page", response.context)


class ToggleFollowViewTest(TestCase):
    """Tests for the toggle_follow view that handles following/unfollowing users."""

    def setUp(self):
        """Create users for testing follow functionality."""
        self.client = Client()
        self.alice = User.objects.create_user(username="alice", password="pass123")
        self.bob = User.objects.create_user(username="bob", password="pass123")

    def test_follow_user_successfully(self):
        """Test that a POST request successfully follows a user."""
        self.client.login(username="alice", password="pass123")
        response = self.client.post(reverse("toggle_follow", args=[self.bob.username]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.bob in self.alice.following.all())

    def test_follow_self_forbidden(self):
        """Test that a user cannot follow themselves."""
        self.client.login(username="alice", password="pass123")
        response = self.client.post(
            reverse("toggle_follow", args=[self.alice.username])
        )
        self.assertEqual(response.status_code, 403)

    def test_unfollow_user_successfully(self):
        """Test that a DELETE request successfully unfollows a user."""
        self.alice.following.add(self.bob)
        self.client.login(username="alice", password="pass123")
        response = self.client.delete(
            reverse("toggle_follow", args=[self.bob.username])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.bob in self.alice.following.all())

    def test_invalid_method_returns_400(self):
        """Test that GET or PUT methods return 400 errors."""
        self.client.login(username="alice", password="pass123")
        response = self.client.get(reverse("toggle_follow", args=[self.bob.username]))
        self.assertEqual(response.status_code, 400)
        response = self.client.put(reverse("toggle_follow", args=[self.bob.username]))
        self.assertEqual(response.status_code, 400)

    def test_toggle_follow_requires_login(self):
        """Test that unauthenticated users cannot toggle follow status."""
        response = self.client.post(reverse("toggle_follow", args=[self.bob.username]))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class ToggleLikeViewTest(TestCase):
    """Tests for the toggle_like view that handles liking/unliking posts."""

    def setUp(self):
        """Create users and a post for like tests."""
        self.client = Client()
        self.alice = User.objects.create_user(username="alice", password="pass123")
        self.bob = User.objects.create_user(username="bob", password="pass123")
        self.bob_post = Post.objects.create(user=self.bob, text="Bob's post")

    def test_like_post_successfully(self):
        """Test that a PUT request likes a post."""
        self.client.login(username="alice", password="pass123")
        response = self.client.put(
            reverse("toggle_like", args=[self.bob_post.id]),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.alice in self.bob_post.likes.all())

    def test_unlike_post_successfully(self):
        """Test that a second PUT unlikes the post."""
        self.bob_post.likes.add(self.alice)
        self.client.login(username="alice", password="pass123")
        response = self.client.put(
            reverse("toggle_like", args=[self.bob_post.id]),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.alice in self.bob_post.likes.all())

    def test_like_own_post_forbidden(self):
        """Test that users cannot like their own post."""
        self.client.login(username="bob", password="pass123")
        response = self.client.put(
            reverse("toggle_like", args=[self.bob_post.id]),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_toggle_like_requires_login(self):
        """Test that unauthenticated users cannot like posts."""
        response = self.client.put(
            reverse("toggle_like", args=[self.bob_post.id]),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_toggle_like_invalid_method_returns_400(self):
        """Test that GET or POST methods return 400 errors."""
        self.client.login(username="alice", password="pass123")
        response = self.client.get(reverse("toggle_like", args=[self.bob_post.id]))
        self.assertEqual(response.status_code, 400)
        response = self.client.post(reverse("toggle_like", args=[self.bob_post.id]))
        self.assertEqual(response.status_code, 400)
