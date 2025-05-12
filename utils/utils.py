from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
import os
from django.conf import settings
from django.contrib.staticfiles import finders

def fetch_resources(uri, rel):
    """
    Converts HTML URIs to absolute system paths so xhtml2pdf can access those resources
    """
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = finders.find(uri.replace(settings.STATIC_URL, ""))
    else:
        return uri  # for http:// or https:// links

    if not os.path.isfile(path):
        raise Exception(f'Media URI must start with {settings.MEDIA_URL} or {settings.STATIC_URL}')
    return path



def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None

def calculate_invoice_totals(invoice):
    subtotal = sum(item.total for item in invoice.items.all())
    tax_amount = subtotal * (invoice.tax / 100)
    total_amount = subtotal + tax_amount - invoice.discount
    return {
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
    }