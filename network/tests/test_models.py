"""Test User and Post model methods."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from network.models import Post

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model methods."""

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="test123")
        self.bob = User.objects.create_user(username="bob", password="test123")

    def test_num_following_and_followers(self):
        """Test to ensure number following and followers."""
        self.alice.following.add(self.bob)
        self.assertEqual(self.alice.num_following(), 1)
        self.assertEqual(self.bob.num_followers(), 1)

    def test_user_cannot_follow_self(self):
        """Test to ensure users can't follow themselves."""
        with self.assertRaises(ValidationError):
            self.alice.following.add(self.alice)

    def test_user_can_follow_others(self):
        """Test to ensure users can follow other users."""
        self.alice.following.add(self.bob)
        self.assertEqual(self.alice.following.count(), 1)
        self.assertEqual(self.bob.followers.count(), 1)

    def test_user_str_returns_username(self):
        """Test to ensure converting user to string returns username."""
        self.assertEqual(str(self.alice), "alice")


class PostModelTest(TestCase):
    """Test Post model methods."""

    def setUp(self):
        self.user = User.objects.create_user(username="charlie", password="test123")
        self.other_user = User.objects.create_user(username="dave", password="test123")

    def test_post_ordering(self):
        """Test to ensure converting post ordering."""
        now = timezone.now()
        post1 = Post.objects.create(user=self.user, text="First post", created=now)
        post2 = Post.objects.create(
            user=self.user, text="Second post", created=now + timedelta(seconds=1)
        )

        posts = list(Post.objects.all())
        self.assertEqual(posts[0], post2)
        self.assertEqual(posts[1], post1)

    def test_post_str_output_short_text(self):
        """Test to ensure converting post to string returns the text and username."""
        post = Post.objects.create(user=self.user, text="Short post")
        self.assertEqual(str(post), "Short post by charlie")

    def test_post_str_output_truncated_text(self):
        """Test to ensure converting long post to string truncates correctly."""
        long_text = "This is a really long post that should be truncated in __str__"
        post = Post.objects.create(user=self.user, text=long_text)
        self.assertTrue(str(post).startswith("This is a really"))
        self.assertIn("by charlie", str(post))
        self.assertIn("...", str(post))

    def test_post_was_edited_flag(self):
        """Test to ensure editing the post's text sets was_edited flag correctly."""
        post = Post.objects.create(user=self.user, text="Initial text")
        post.text = "Updated text"
        post.save()
        post.refresh_from_db()
        self.assertTrue(post.was_edited)

    def test_post_with_empty_text_raises_error(self):
        """Test to ensure a post with empty text raises a validation error."""
        with self.assertRaises(ValidationError):
            post = Post(user=self.user, text="    ")
            post.full_clean()

    def test_post_with_empty_edited_text_raises_error(self):
        """Test to ensure changing a post's text to empty raises a validation error."""
        with self.assertRaises(ValidationError):
            post = Post(user=self.user, text="Initial text")
            post.text = "    "
            post.full_clean()

    def test_user_cannot_like_own_post(self):
        """Test to ensure users can't like their own posts."""
        post = Post.objects.create(user=self.user, text="My own post")
        with self.assertRaises(ValidationError):
            post.likes.add(self.user)

    def test_user_can_like_other_post(self):
        """Test to ensure users can like other user's posts."""
        post = Post.objects.create(user=self.user, text="Another post")
        post.likes.add(self.other_user)
        self.assertEqual(post.likes.count(), 1)
        self.assertEqual(self.other_user.liked_posts.count(), 1)

    def test_user_cannot_like_post_multiple_times(self):
        """Test to ensure users cannot like same post twice."""
        post = Post.objects.create(user=self.user, text="Another post")
        post.likes.add(self.other_user)
        post.likes.add(self.other_user)  # Should not duplicate
        self.assertEqual(post.likes.count(), 1)
