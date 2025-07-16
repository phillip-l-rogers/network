from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("compose", views.compose, name="compose"),
    path("edit/<int:post_id>", views.edit_post, name="edit_post"),
    path("follow/<str:username>", views.toggle_follow, name="toggle_follow"),
    path("like/<int:post_id>", views.toggle_like, name="toggle_like"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("profile/<str:username>", views.profile, name="profile"),
    path("register", views.register, name="register"),
]
