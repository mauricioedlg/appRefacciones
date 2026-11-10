from django.http import Http404
from django.shortcuts import render
from django.template import TemplateDoesNotExist


def pagina_frontend(request, pagina='index.html'):
    try:
        return render(request, pagina)
    except TemplateDoesNotExist as exc:
        raise Http404('Página no encontrada.') from exc
