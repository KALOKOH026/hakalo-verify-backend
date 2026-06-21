from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import HelloSerializer

class HelloView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = {"message": f"Hello, {request.user.username}!"}
        serializer = HelloSerializer(payload)
        return Response(serializer.data)
