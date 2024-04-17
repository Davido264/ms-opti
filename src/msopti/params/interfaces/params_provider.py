"""
Intefaz principal para proveer la información necesaria para el algoritmo
"""

import abc
from msopti.params.interfaces.stop_provider import IStopProvider
from msopti.params.interfaces.route_provider import IRouteProvider
from msopti.params.interfaces.schedule_provider import IScheduleProvider
from msopti.params.interfaces.scores_provider import IScoreProvider
from msopti.params.interfaces.vehicle_provider import IVehicleProvider


class IParamsProvider(abc.ABC):
    """
    Información de los parámetros y configuraciones en el cual el
    algoritmo va a trabajar.
    """

    @property
    @abc.abstractmethod
    def stops(self) -> tuple[IStopProvider]:
        """
        Una tupla (inmutable) de paradas, la información de todas las paradas.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def routes(self) -> tuple[IRouteProvider]:
        """
        Una tupla (inmutable) de rutas, la información de todas las rutas.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def schedule(self) -> IScheduleProvider:
        """
        Los parámetros de la jornada del día.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def scores(self) -> IScoreProvider:
        """
        Los parámetros para las penalizaciones.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def vehicles(self) -> tuple[IVehicleProvider]:
        """
        Una tupla (inmutable) de vehículos, la información de todas las unidades
            de transporte.
        """
        raise NotImplementedError
