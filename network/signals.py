"""Signals to add to the models."""

import logging

from django.core.exceptions import ValidationError
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(m2m_changed)
def prevent_self_follow(sender, instance, action, pk_set, **kwargs):
    """Signal that validates the following relationship before adding it."""
    if not instance.pk or not pk_set:
        return
    from .models import User  # Import here, safely

    if sender == User.following.through and action == "pre_add":
        if instance.pk in pk_set:
            logger.warning(f"User {instance} attempted to follow themselves.")
            raise ValidationError("Users cannot follow themselves.")


@receiver(m2m_changed)
def prevent_self_like(sender, instance, action, pk_set, **kwargs):
    """Signal that validates the following relationship before adding it."""
    if not instance.pk or not pk_set:
        return
    from .models import Post  # Import here, safely

    if sender == Post.likes.through and action == "pre_add":
        if instance.user.pk in pk_set:
            logger.warning(
                f"User {instance.user} attempted to like own post {instance.pk}."
            )
            raise ValidationError("Users cannot like own posts.")
