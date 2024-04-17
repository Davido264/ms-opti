"""
Interfaz para proveer la información sobre los horarios.
"""

import abc
import datetime
from msopti.params.interfaces.lunch_schedule_provider import ILunchScheduleProvider
from msopti.params.interfaces.schedule_limits_provider import IScheduleLimitsProvider


class IScheduleProvider(abc.ABC):
    """Descripción de los horarios manejados en un día.

    El inicio y el final de la jornada vienen indicados como `ScheduleLimits`
    y representan la hora mínima a la que debe iniciar/terminar el primer
    recorrido, y la hora máxima a la que debe iniciar/terminal el último
    recorrido.
    """

    @property
    @abc.abstractmethod
    def start(self) -> IScheduleLimitsProvider:
        """
        Valores mínimos y máximos para el inicio de la jornada.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def end(self) -> IScheduleLimitsProvider:
        """
        Valores mínimos y máximos para la finalización de la jornada.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def rests(self) -> IScheduleLimitsProvider:
        """
        Valores mínimos y máximos para el tiempo designado para descansar entre
            viaje y viaje.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def lunch(self) -> ILunchScheduleProvider:
        """
        Los horarios del almuerzo.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def interval(self) -> datetime.timedelta:
        """
        Intervalo de tiempo mínimo para reintentar despachar.
        """
        raise NotImplementedError
