import numpy as np
from scipy.stats import uniform, expon

def uniform_distribution(rate: float, size: int) -> np.ndarray:
    """
    Distribución uniforme para intervalos entre consultas.
    Args:
        rate: Tasa promedio de consultas por segundo (ej: 2.0 para ~2 consultas/seg)
        size: Número de muestras a generar
    Returns:
        Array de tiempos de espera en segundos
    """
    scale = 1.0 / rate  # Intervalo promedio entre consultas
    return uniform(loc=0, scale=2*scale).rvs(size)  # Rango [0, 2*(1/rate)]

def exponential_distribution(rate: float, size: int) -> np.ndarray:
    """
    Distribución exponencial (para eventos independientes).
    Args:
        rate: Lambda (consultas/segundo)
        size: Número de muestras
    Returns:
        Array de tiempos entre llegadas en segundos
    """
    return expon(scale=1/rate).rvs(size)  # scale = 1/lambda