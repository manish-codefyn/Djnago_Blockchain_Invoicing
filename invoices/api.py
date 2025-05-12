from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import Invoice
from .serializers import InvoiceSerializer
from .blockchain import Blockchain
import logging

logger = logging.getLogger(__name__)

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    @action(detail=True, methods=['get'])
    def verify(self, request, pk=None):
        invoice = self.get_object()
        
        try:
            blockchain = Blockchain()
            
            # Search through all blocks for this invoice's transaction
            found = False
            for block in blockchain.chain:
                for tx in block.get('transactions', []):
                    if tx.get('invoice_id') == str(invoice.id):
                        found = True
                        # Verify the hash
                        calculated_hash = blockchain.hash(block)
                        if calculated_hash == invoice.blockchain_hash:
                            return Response({
                                'verified': True,
                                'block_index': block['index'],
                                'timestamp': block['timestamp'],
                                'details': tx
                            })
                        else:
                            return Response({
                                'verified': False,
                                'error': 'Hash mismatch'
                            }, status=status.HTTP_400_BAD_REQUEST)
            
            if not found:
                return Response({
                    'verified': False,
                    'error': 'Transaction not found in blockchain'
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Blockchain verification failed for invoice {invoice.id}: {e}")
            return Response({
                'verified': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def blockchain_status(self, request):
        try:
            blockchain = Blockchain()
            return Response({
                'chain_length': len(blockchain.chain),
                'last_block': blockchain.last_block['index'],
                'last_block_hash': blockchain.hash(blockchain.last_block),
                'nodes': list(blockchain.nodes)
            })
        except Exception as e:
            logger.error(f"Failed to get blockchain status: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)