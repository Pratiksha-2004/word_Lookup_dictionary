from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('search-word/', views.search_word, name='search_word'),
    path('search-history/', views.search_history, name='search_history'),
    path('total-searches/', views.total_searches, name='total_searches'),

    # Auth
    path('login/', views.login_view, name='login_page'),
    path('register/', views.register_view, name='register_page'),
    path('logout/', LogoutView.as_view(next_page='login_page'), name='logout'),  # ← changed here
]
