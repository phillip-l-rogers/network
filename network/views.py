"""Provide the functions for the urls for the various views."""

import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from network.models import Post

from .models import Post, User


@login_required
def compose(request: HttpRequest) -> JsonResponse:
    """Create a new post."""
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    try:
        data = json.loads(request.body)
        text = data.get("text", "").strip()
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    if not text:
        return JsonResponse({"error": "Post text cannot be empty."}, status=400)
    post = Post(user=request.user, text=text)
    post.save()
    return JsonResponse(
        {
            "message": "Post created successfully.",
            "post_id": post.id,
            "created": post.created,
            "text": post.text,
            "username": request.user.username,
        },
        status=201,
    )


@login_required
def edit_post(request: HttpRequest, post_id: int) -> JsonResponse:
    """Edit an existing post"""
    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required."}, status=400)
    post = get_object_or_404(Post, pk=post_id)
    # Ensure only the author can edit
    if post.user != request.user:
        return JsonResponse({"error": "You can only edit your own posts."}, status=403)
    try:
        data = json.loads(request.body)
        new_text = data.get("text", "").strip()
        if not new_text:
            return JsonResponse({"error": "Text cannot be empty."}, status=400)
        post.text = new_text
        post.save()
        return JsonResponse(
            {
                "message": "Post updated successfully.",
                "was_edited": post.was_edited,
                "new_text": post.text,
            }
        )
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)


def index(request: HttpRequest) -> HttpResponse:
    """Show all posts."""
    posts = Post.objects.all().prefetch_related("likes")
    paginator = Paginator(posts, 10)  # 10 posts per page
    i_page = request.GET.get("page") or 1
    page = paginator.get_page(i_page)
    return render(request, "network/index.html", {"page": page})


def login_view(request: HttpRequest) -> HttpResponse:
    """
    Handle the login get/post request.

    Redirect to login page if get request or problems signing in.
    Otherwise, redirect to the index page.
    """
    if request.method != "POST":
        return render(request, "network/login.html")
    # Attempt to sign user in
    username = request.POST["username"]
    password = request.POST["password"]
    user = authenticate(request, username=username, password=password)
    # Check if authentication successful
    if user is None:
        return render(
            request,
            "network/login.html",
            {"message": "Invalid username and/or password."},
        )
    login(request, user)
    return HttpResponseRedirect(reverse("index"))


def logout_view(request: HttpRequest) -> HttpResponse:
    """Handle the logout request and redirect back to index."""
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def profile(request: HttpRequest, username: str) -> HttpResponse:
    """Show the profile for a user."""
    user = get_object_or_404(User, username=username)
    posts = user.posts.prefetch_related("likes").select_related("user")
    paginator = Paginator(posts, 10)  # 10 posts per page
    i_page = request.GET.get("page") or 1
    page = paginator.get_page(i_page)
    is_following = False
    is_own_profile = False
    if request.user.is_authenticated:
        is_following = request.user.following.filter(pk=user.pk).exists()
        is_own_profile = request.user == user
    return render(
        request,
        "network/profile.html",
        {
            "user": user,
            "page": page,
            "is_following": is_following,
            "is_own_profile": is_own_profile,
        },
    )


def register(request: HttpRequest) -> HttpResponse:
    """
    Handle the register get/post request.

    Redirect to register page if get request or problems registering.
    Otherwise, redirect to the index page.
    """
    if request.method != "POST":
        return render(request, "network/register.html")
    username = request.POST["username"]
    email = request.POST["email"]
    # Ensure password matches confirmation
    password = request.POST["password"]
    confirmation = request.POST["confirmation"]
    if password != confirmation:
        return render(
            request, "network/register.html", {"message": "Passwords must match."}
        )
    # Attempt to create new user
    try:
        user = User.objects.create_user(username, email, password)
        user.save()
    except IntegrityError:
        return render(
            request, "network/register.html", {"message": "Username already taken."}
        )
    login(request, user)
    return HttpResponseRedirect(reverse("index"))


@login_required
def toggle_follow(request: HttpRequest, username: str) -> JsonResponse:
    """Toggle the follow status for an existing user."""
    if request.method not in ("DELETE", "POST"):
        return JsonResponse({"error": "DELETE or POST request required."}, status=400)
    user = get_object_or_404(User, username=username)
    if user == request.user:
        return JsonResponse({"error": "You can't follow yourself."}, status=403)
    # Current following status
    following = request.user.following.filter(pk=user.pk).exists()
    if following and request.method != "DELETE":
        return JsonResponse({"error": "DELETE request required."}, status=400)
    if not following and request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    # Toggle status
    following = not following
    if following:
        request.user.following.add(user)
    else:
        request.user.following.remove(user)
    return JsonResponse(
        {
            "message": "User following toggled successfully.",
            "following": following,
            "num_followers": user.num_followers(),
        }
    )


@login_required
def toggle_like(request: HttpRequest, post_id: int) -> JsonResponse:
    """Toggle the like status on an existing post"""
    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required."}, status=400)
    post = get_object_or_404(Post, pk=post_id)
    if post.user == request.user:
        return JsonResponse({"error": "You can't like your own posts."}, status=403)
    # Current liked status
    liked = post.likes.filter(pk=request.user.pk).exists()
    # Toggle status
    liked = not liked
    if liked:
        post.likes.add(request.user)
    else:
        post.likes.remove(request.user)
    return JsonResponse(
        {
            "message": "Post like toggled successfully.",
            "liked": liked,
            "num_likes": post.likes.count(),
        }
    )
