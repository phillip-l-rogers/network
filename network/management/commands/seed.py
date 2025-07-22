# network/management/commands/seed.py

import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from network.models import Post

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with test users, posts, likes, and follows"

    def handle(self, *args, **options):
        # Create test users
        usernames = ["alice", "bob", "charlie"]
        for username in usernames:
            if not User.objects.filter(username=username).exists():
                email = f"{username}@example.com"
                User.objects.create_user(
                    username=username, email=email, password="testpass"
                )
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
        for user in (alice, bob, charlie):
            for _ in range(3):  # 3 posts per user
                Post.objects.create(
                    user=user,
                    text=random.choice(content_samples),
                )
        self.stdout.write(self.style.SUCCESS("✅ Posts created"))
        # Create follows (alice follows bob and charlie)
        for user in (bob, charlie):
            alice.following.add(user)
        self.stdout.write(self.style.SUCCESS("✅ Follow relationships created"))
        # Random likes: bob likes alice's posts, charlie likes bob's
        for post in Post.objects.filter(user=alice):
            post.likes.add(bob)
        for post in Post.objects.filter(user=bob):
            post.likes.add(charlie)
        self.stdout.write(self.style.SUCCESS("✅ Likes added"))
