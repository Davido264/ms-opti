"""
Interfaz para proveer la información necesaria para los descansos por almuerzo
"""

import abc
import datetime


class ILunchScheduleProvider(abc.ABC):
    """Descripción de los horarios para el almuerzo.

    Se contempla que el almuerzo no se dará a la misma hora, sino que
    se enviará a los almuerzos paulatinamente. Los tiempos dados son
    representados como distancias de tiempo desde las 00:00:00.
    """

    @property
    @abc.abstractmethod
    def time(self) -> datetime.timedelta:
        """
        El tiempo que de tiene predefinido para almuerzos.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def start(self) -> datetime.timedelta:
        """
        La hora mínima para que se tenga el **primer** almuerzo desde las
            00:00:00.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def end(self) -> datetime.timedelta:
        """
        Returns:
            end: La hora máxima para que se tenga el **último** almuerzo
                desde las 00:00:00.
        """
        raise NotImplementedError
