# Ejecutor aislado (ADR-005). Construir desde la raíz del proyecto:
#   docker build -f ejecutor/Dockerfile -t idc-ejecutor .
# [VERIFICAR en F9: fijar la imagen base por digest antes de desplegar.]
FROM python:3.12-slim

WORKDIR /app
COPY refuerzo/servicios/corredor.py ejecutor/servidor.py /app/

# Usuario sin privilegios. En ejecución se añaden --read-only, --tmpfs /tmp,
# --cap-drop ALL, --security-opt no-new-privileges y los límites de 08 §2.2.
USER 65534:65534
EXPOSE 8080

# Forma exec: el servidor queda como proceso 1, inmune a las señales del código ejecutado.
CMD ["python", "-I", "/app/servidor.py"]
