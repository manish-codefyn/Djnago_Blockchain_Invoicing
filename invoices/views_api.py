from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Invoice, Client
from .serializers import InvoiceSerializer, ClientSerializer
from .blockchain.blockchain import Blockchain

class InvoiceListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class InvoiceRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.status == 'paid' and not instance.blockchain_hash:
            instance.add_to_blockchain()

class ClientListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Client.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ClientRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Client.objects.filter(user=self.request.user)

class BlockchainView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        blockchain = Blockchain()
        response = {
            'chain': blockchain.chain,
            'length': len(blockchain.chain),
        }
        return Response(response, status=status.HTTP_200_OK)