from django.conf import settings

from refuerzo.acceso import SESION_ESTUDIANTE


def perfil(request):
    return {
        "perfil": settings.PERFIL,
        "estudiante_activo": SESION_ESTUDIANTE in request.session,
    }
