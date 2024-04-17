"""
Intefaz para proveer información sobre un vehículo
"""

import abc

class IVehicleProvider(abc.ABC):
    """
    Información sobre un Vehículo.
    """

    @property
    @abc.abstractmethod
    def unumber(self) -> int:
        """
        El número de la unidad.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def min(self) -> int:
        """
        La capacidad mínima de pasajeros que puede llevar.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def max(self) -> int:
        """
        La capacidad máxima de pasajeros que puede llevar.
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def is_available(self) -> bool:
        """
        `True` si la unidad está disponible para realizar recorridos, `False`
        si no lo está.
        """
        raise NotImplementedError

    @is_available.setter
    @abc.abstractmethod
    def is_available(self,available: bool):
        """
        Define un nuevo valor para la disponibilidad de una unidad.

        Arguments:
            available: `True` si la unidad está disponible para realizar 
                recorridos, `False` si no lo está.
        """
        raise NotImplementedError


    @property
    @abc.abstractmethod
    def route_id(self) -> str | int:
        """
        El id de la ruta que la unidad sigue (string o int).
        """
        raise NotImplementedError
