"""
Interfaz para proveer la información necesaria sobre los límites en los horarios
"""

import abc
import datetime

class IScheduleLimitsProvider(abc.ABC):
    """Límite superior e inferior de un horario.

    Contiene mínimo y máximo para distintos horarios los valores son
    representados como distancias de tiempo a partir de las 00:00:00.
    """

    @property
    @abc.abstractmethod
    def min(self) -> datetime.timedelta:
        """
        Valor mínimo de tiempo desde las 00:00:00.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def max(self) -> datetime.timedelta:
        """
        Valor máxima de tiempo desde las 00:00:00.
        """
        raise NotImplementedError
