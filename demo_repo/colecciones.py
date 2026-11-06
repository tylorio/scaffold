"""Tareas de estructuras de datos: mezcla de estilos."""
from collections import deque


def group_students_by_grade(student_records: list[dict]) -> dict[str, list]:
    """Agrupa estudiantes según su nota.

    Args:
        student_records (list[dict]): Registros con nombre y nota.

    Returns:
        dict[str, list]: Estudiantes agrupados por nota.
    """
    grouped_students = {}
    # Procesa cada registro de estudiante
    for student_record in student_records:
        # Crea el grupo si todavía no existe
        grouped_students.setdefault(student_record["nota"], []).append(student_record)
    return grouped_students


def find_common_elements(first_items: list, second_items: list) -> list:
    """Obtiene los elementos presentes en ambas listas.

    Args:
        first_items (list): Primera lista.
        second_items (list): Segunda lista.

    Returns:
        list: Elementos comunes ordenados.
    """
    # Convierte las listas a conjuntos para la intersección
    return sorted(set(first_items) & set(second_items))


def invert_dictionary_mapping(source_mapping: dict) -> dict:
    """Invierte las claves y los valores de un diccionario.

    Args:
        source_mapping (dict): Diccionario original.

    Returns:
        dict: Diccionario invertido.
    """
    # Construye el resultado con una comprensión
    return {value: key for key, value in source_mapping.items()}


class Cola:
    def __init__(self):
        self.d = deque()

    def meter(self, x):
        self.d.append(x)

    def sacar(self):
        return self.d.popleft()

    def __len__(self):
        return len(self.d)
