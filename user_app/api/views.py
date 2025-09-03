from rest_framework.decorators import api_view
from user_app.api.serializers import RegisterUserSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from Book_app.api.audit import log_action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
# from rest_framework.authtoken.views import obtain_auth_token
# from rest_framework.authtoken.models import Token

@api_view(['POST'])
def register_user_view(request):
    """
    Register a new user.
    """
    serializer = RegisterUserSerializer(data=request.data)
    data = {}
    if serializer.is_valid():
        user = serializer.save()
        
        data['username'] = user.username
        data['email'] = user.email
    
        refresh = RefreshToken.for_user(user)
        data['token'] = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                }
        
        # log the action
        log_action(
            user=user,
            action="USER_REGISTERED",
            details=f"New user registered: {user.username} ({user.email})"
        )

            # token = Token.objects.create(user=user)
            
        return Response({
                        "message": "User registered successfully",
                        "data": data
                        },
                        
                        status=status.HTTP_201_CREATED
                        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# def logout_view(request):
#     if request.method == 'POST':
#         request.user.auth_token.delete()  # Delete old token if it exists
#         return Response(status=status.HTTP_200_OK)
    
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()   # mark it as blacklisted
            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)