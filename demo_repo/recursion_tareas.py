"""Tareas de recursión: estilo muy documentado, agregado en un solo commit grande."""


def calculate_fibonacci_number(position_index: int) -> int:
    """Calcula el número de Fibonacci en la posición indicada.

    Args:
        position_index (int): Posición dentro de la secuencia.

    Returns:
        int: Valor de Fibonacci en esa posición.
    """
    # Caso base de la recursión
    if position_index < 2:
        return position_index
    # Caso recursivo
    return calculate_fibonacci_number(position_index - 1) + calculate_fibonacci_number(position_index - 2)


def calculate_greatest_common_divisor(first_number: int, second_number: int) -> int:
    """Calcula el máximo común divisor con el algoritmo de Euclides.

    Args:
        first_number (int): Primer número.
        second_number (int): Segundo número.

    Returns:
        int: Máximo común divisor.
    """
    # Caso base: el segundo número es cero
    if second_number == 0:
        return first_number
    # Reduce el problema con el residuo
    return calculate_greatest_common_divisor(second_number, first_number % second_number)


def compute_power_recursively(base_value: float, exponent_value: int) -> float:
    """Eleva un número a una potencia de forma recursiva.

    Args:
        base_value (float): Base de la potencia.
        exponent_value (int): Exponente no negativo.

    Returns:
        float: Resultado de la potencia.
    """
    # Caso base: todo número elevado a cero es uno
    if exponent_value == 0:
        return 1
    # Multiplica la base por la potencia reducida
    return base_value * compute_power_recursively(base_value, exponent_value - 1)


def count_nested_elements(nested_items: list) -> int:
    """Cuenta los elementos de una lista anidada.

    Args:
        nested_items (list): Lista que puede contener otras listas.

    Returns:
        int: Cantidad total de elementos.
    """
    total_count = 0
    # Recorre cada elemento de la lista
    for current_item in nested_items:
        if isinstance(current_item, list):
            # Llamada recursiva para la sublista
            total_count += count_nested_elements(current_item)
        else:
            total_count += 1
    return total_count
