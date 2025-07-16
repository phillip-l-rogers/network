"""Models for the network app."""

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    """Custom user model that adds following/followers."""

    class Meta:
        """Explicitly set the verbose name and plural name."""

        verbose_name = "user"
        verbose_name_plural = "users"

    following = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="followers"
    )

    def __str__(self):
        """Return the username when converting to string."""
        return str(self.username)

    def clean(self):
        """Called during validation to ensure not self-following."""
        if self.pk and self.following.filter(pk=self.pk).exists():
            raise ValidationError("Users cannot follow themselves.")

    def num_following(self) -> int:
        """Return the number of users the User is following."""
        return self.following.count()

    def num_followers(self) -> int:
        """Return the number of users who are following the User."""
        return self.followers.count()

    def save(self, *args, **kwargs):
        """Custom save method to ensure clean() runs on save."""
        self.full_clean()
        super().save(*args, **kwargs)


class Post(models.Model):
    """Model for a post which includes the user, text, created fields, and likes"""

    class Meta:
        """Explicitly set the default ordering, verbose name and plural name."""

        ordering = ["-created"]
        verbose_name = "post"
        verbose_name_plural = "posts"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    likes = models.ManyToManyField(User, blank=True, related_name="liked_posts")
    text = models.CharField(max_length=512, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    was_edited = models.BooleanField(default=False)

    def __str__(self) -> str:
        """Return the text and username truncated if necessary converted to string."""
        if len(self.text) > 25:
            return f"{self.text[:20]}... by {self.user}"
        return f"{self.text} by {self.user}"

    def clean(self):
        """Custom clean method tp prevent users from liking their own posts."""
        if not self.text.strip():
            raise ValidationError("Post text cannot be empty or whitespace.")
        if self.pk and self.likes.filter(pk=self.pk).exists():
            raise ValidationError("Users cannot like their own posts.")

    def num_likes(self) -> int:
        """Return the number of likes for the `Post`."""
        return self.likes.count()

    def save(self, *args, **kwargs):
        """Custom save method to ensure clean() runs on save."""
        if self.pk and Post.objects.filter(pk=self.pk).exists():
            original = Post.objects.get(pk=self.pk)
            if original.text != self.text:
                self.was_edited = True
        self.full_clean()
        super().save(*args, **kwargs)
