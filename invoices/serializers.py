from rest_framework import serializers
from .models import Invoice, InvoiceItem, Client

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['id', 'description', 'quantity', 'unit_price', 'tax', 'total']

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'phone', 'address', 'tax_id', 'notes']

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    client = ClientSerializer(read_only=True)
    client_id = serializers.UUIDField(write_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    blockchain_hash = serializers.CharField(read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'client', 'client_id', 'date_issued', 'due_date', 
            'status', 'notes', 'terms', 'tax', 'discount', 'items', 'subtotal', 
            'tax_amount', 'total_amount', 'blockchain_hash', 'created_at', 'updated_at'
        ]
    
    def validate_client_id(self, value):
        if not Client.objects.filter(id=value, user=self.context['request'].user).exists():
            raise serializers.ValidationError("Client not found.")
        return value
    
    def create(self, validated_data):
        validated_data['client'] = Client.objects.get(id=validated_data.pop('client_id'))
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'client_id' in validated_data:
            instance.client = Client.objects.get(id=validated_data.pop('client_id'))
        return super().update(instance, validated_data)