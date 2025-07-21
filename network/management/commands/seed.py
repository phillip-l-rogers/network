# network/management/commands/seed.py

import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from network.models import Post

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with test users, posts, likes, and follows"

    def handle(self, *args, **options):
        # Create test users
        users_data = [
            {"username": "alice", "email": "alice@example.com"},
            {"username": "bob", "email": "bob@example.com"},
            {"username": "charlie", "email": "charlie@example.com"},
        ]
        users = []
        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data["username"], defaults={"email": data["email"]}
            )
            if created:
                user.set_password("testpass")
                user.save()
            users.append(user)
        alice = User.objects.get(username="alice")
        bob = User.objects.get(username="bob")
        charlie = User.objects.get(username="charlie")
        self.stdout.write(self.style.SUCCESS("✅ Users created"))
        # Create posts
        content_samples = [
            "Hello, world!",
            "Just setting up my network app.",
            "What’s everyone coding today?",
            "Check out my new Django project!",
            "Writing some seed data 💾",
            "Feeling productive today!",
        ]
        for user in users:
            for _ in range(3):  # 3 posts per user
                Post.objects.create(
                    user=user,
                    text=random.choice(content_samples),
                    timestamp=timezone.now(),
                )
        self.stdout.write(self.style.SUCCESS("✅ Posts created"))
        # Create follows (alice follows bob and charlie)
        for user in (bob, charlie):
            alice.following.add(user)
        self.stdout.write(self.style.SUCCESS("✅ Follow relationships created"))
        # Random likes: bob likes alice's posts, charlie likes bob's
        for post in Post.objects.filter(author=alice):
            post.likes.add(bob)
        for post in Post.objects.filter(author=bob):
            post.likes.add(charlie)
        self.stdout.write(self.style.SUCCESS("✅ Likes added"))
