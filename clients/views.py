from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView,View
from django.urls import reverse_lazy
from .models import Client
from .forms import ClientForm
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ProtectedError



class ClientListView(ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 10


class ClientDetailView(DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('clients:client_list')

    def form_valid(self, form):
        form.instance.user = self.request.user  # Associate client with the logged-in user
        messages.success(self.request, 'Client created successfully!')  # Add success message
        return super().form_valid(form)

class ClientUpdateView(UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('clients:client_list')

    def form_valid(self, form):
        messages.success(self.request, 'Client updated successfully!')
        return super().form_valid(form)
    

class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = 'clients/confirm_delete.html'
    success_url = reverse_lazy('clients:client_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            messages.success(request, 'Client deleted successfully!')
        except ProtectedError as e:
            related_invoices = e.protected_objects
            invoice_list = ', '.join(str(invoice) for invoice in related_invoices)
            messages.error(
                request,
                f'Cannot delete client. This client is linked to invoice(s): {invoice_list}.'
            )
        return HttpResponseRedirect(self.success_url)
