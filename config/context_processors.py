from django.conf import settings


def perfil(request):
    return {"perfil": settings.PERFIL}
