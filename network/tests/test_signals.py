"""Test Signal functions."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import TestCase

from network.models import Post

User = get_user_model()


class SignalTest(TestCase):
    """Test signals functions."""

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="test123")
        self.bob = User.objects.create_user(username="bob", password="test123")
        self.post = Post.objects.create(user=self.bob, text="Bob's post")

    def test_allow_follow_others(self):
        """Test to ensure users can follow other users."""
        self.alice.following.add(self.bob)
        self.assertEqual(self.alice.following.count(), 1)

    def test_allow_like_others_post(self):
        """Test to ensure users can like other user's posts."""
        self.post.likes.add(self.alice)
        self.assertEqual(self.post.likes.count(), 1)

    def test_multiple_valid_follows(self):
        """Test to ensure adding multiple followers works correctly."""
        charlie = User.objects.create_user(username="charlie", password="test123")
        self.alice.following.add(self.bob, charlie)
        self.assertEqual(self.alice.following.count(), 2)

    def test_multiple_valid_likes(self):
        """Test to ensure adding multiple likes works correctly."""
        charlie = User.objects.create_user(username="charlie", password="test123")
        self.post.likes.add(self.alice, charlie)
        self.assertEqual(self.post.likes.count(), 2)

    def test_prevent_self_follow_signal(self):
        """Test to ensure users can't follow themselves."""
        with self.assertRaises(ValidationError):
            self.alice.following.add(self.alice)

    def test_prevent_self_like_signal(self):
        """Test to ensure users can't like their own posts."""
        own_post = Post.objects.create(user=self.alice, text="Alice's post")
        with self.assertRaises(ValidationError):
            own_post.likes.add(self.alice)

    def test_self_follow_blocks_all_in_bulk(self):
        """Test that self-follow doesn’t block others in bulk"""
        charlie = User.objects.create_user(username="charlie", password="test123")
        with self.assertRaises(ValidationError):
            with transaction.atomic():
                self.alice.following.add(self.alice, charlie)
        self.post.refresh_from_db()
        self.assertEqual(self.alice.following.count(), 0)

    def test_self_like_blocks_all_in_bulk(self):
        """Test that self-like doesn’t block others in bulk"""
        self.post.user = self.alice
        self.post.save()
        charlie = User.objects.create_user(username="charlie", password="test123")
        with self.assertRaises(ValidationError):
            with transaction.atomic():
                self.post.likes.add(self.alice, charlie)
        self.post.refresh_from_db()
        self.assertEqual(self.post.likes.count(), 0)
