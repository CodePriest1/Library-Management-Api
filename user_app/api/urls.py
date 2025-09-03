# from rest_framework.authtoken.views import obtain_auth_token 
from user_app.api.views import register_user_view
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from user_app.api.views import LogoutView


# urlpatterns = [
#     # # path('login/', obtain_auth_token, name='login'),  # Token authentication endpoint
#     path('register/', register_user_view, name='register'),  # User registration endpoint
#     path('logout/', LogoutView.as_view(), name='logout'),  # User logout endpoint
    
#     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh')

urlpatterns = [
    # JWT endpoints
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # dj-rest-auth endpoints
    path("auth/", include("dj_rest_auth.urls")),  # login/logout/password reset
    path("auth/registration/", include("dj_rest_auth.registration.urls")),  # signup

    # social login (Google/GitHub)
    path("auth/social/", include("allauth.urls")),  
]

