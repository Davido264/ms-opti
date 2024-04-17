"""Configuraciones y variables para el algoritmo."""

import json
import datetime
from dataclasses import dataclass
import dataclass_wizard as dw

from typing import final

from msopti.params.interfaces.route_provider import IRouteProvider
from msopti.params.interfaces.schedule_limits_provider import IScheduleLimitsProvider
from msopti.params.interfaces.schedule_provider import IScheduleProvider
from msopti.params.interfaces.scores_provider import IScoreProvider
from msopti.params.interfaces.stop_provider import IStopProvider
from msopti.params.interfaces.lunch_schedule_provider import ILunchScheduleProvider
from msopti.params.interfaces.vehicle_provider import IVehicleProvider
from msopti.params.interfaces.params_provider import IParamsProvider

# datatypes
@final
@dataclass
class Stop(IStopProvider):
    """
    Attributes:
        id: Un ID en string o int.
        name: El nombre de la parada.
        time: El tiempo que demora **normalmente** el recorrido desde
            la parada anterior a la parada actual.
        event_delay: El tiempo adicional que tardará el transporte en llegar
            a la parada, (por defecto 0, modificado dinámicamente).
        last_visit: El tiempo en que la parada fue visitada por última vez.
    """

    _id: str | int = dw.json_field("id", all=True)  # type: ignore
    _name: str = dw.json_field("nombre", all=True)  # type: ignore
    _time: datetime.timedelta = dw.json_field("tiempo", all=True)  # type: ignore pylint: disable=C0301
    _event_delay: datetime.timedelta = dw.json_field("retrasoPorEvento", all=True, default_factory=datetime.timedelta)  # type: ignore pylint: disable=C0301
    _visits: list[datetime.datetime] = dw.json_field("visitas", dump=False, default_factory=list)  # type: ignore pylint: disable=C0301

    def visit(self,dt: datetime.datetime):
        self._visits.append(dt)
        self._visits.sort()

    @property
    def id(self) -> str|int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def time(self) -> datetime.timedelta:
        return self._time

    @property
    def event_delay(self) -> datetime.timedelta:
        return self._event_delay

    @event_delay.setter
    def event_delay(self, d: datetime.timedelta):
        self._event_delay = d

    @property
    def visits(self) -> tuple[datetime.datetime]:
        return tuple(i for i in self._visits)


@final
@dataclass
class Route(IRouteProvider):
    """
    Attributes:
        id: Un id en string o int.
        stops: Una lista de ids de paradas (strings o ints), indicando las
            paradas que sigue la ruta.
    """

    _id: str | int = dw.json_field("id", all=True)  # type: ignore
    _stops: list[str | int] = dw.json_field("paradas", all=True)  # type: ignore

    @property
    def id(self) -> str|int:
        return self._id

    @property
    def stops(self) -> tuple[str|int]:
        return tuple(i for i in self._stops)


@final
@dataclass
class ScheduleLimits(IScheduleLimitsProvider):
    """
    Attributes:
        min: Valor mínimo de tiempo desde las 00:00:00.
        max: Valor máxima de tiempo desde las 00:00:00.
    """

    _min: datetime.timedelta = dw.json_field("min", all=True)  # type: ignore
    _max: datetime.timedelta = dw.json_field("max", all=True)  # type: ignore

    @property
    def min(self) -> datetime.timedelta:
        return self._min

    @property
    def max(self) -> datetime.timedelta:
        return self._max


@final
@dataclass
class LunchSchedule(ILunchScheduleProvider):
    """Descripción de los horarios para el almuerzo.

    Se contempla que el almuerzo no se dará a la misma hora, sino que
    se enviará a los almuerzos paulatinamente. Los tiempos dados son
    representados como distancias de tiempo desde las 00:00:00.

    Attributes:
        time: El tiempo que de tiene predefinido para almuerzos.
        start: La hora mínima para que se tenga el **primer** almuerzo
            desde las 00:00:00.
        end: La hora máxima para que se tenga el **último** almuerzo
            desde las 00:00:00.
    """

    _time: datetime.timedelta = dw.json_field("tiempo", all=True)  # type: ignore pylint: disable=C0301
    _start: datetime.timedelta = dw.json_field("inicio", all=True)  # type: ignore pylint: disable=C0301
    _end: datetime.timedelta = dw.json_field("fin", all=True)  # type: ignore

    @property
    def time(self) -> datetime.timedelta:
        return self._time

    @property
    def start(self) -> datetime.timedelta:
        return self._start

    @property
    def end(self) -> datetime.timedelta:
        return self._end


@final
@dataclass
class Schedule (IScheduleProvider):
    """
    Attributes:
        start: Valores mínimos y máximos para el inicio de la jornada.
        end: Valores mínimos y máximos para la finalización de la jornada.
        rest: Valores mínimos y máximos para el tiempo designado para
            descansar entre viaje y viaje.
        lunch: Los horarios del almuerzo.
        interval: Intervalo de tiempo mínimo para reintentar despachar.
    """

    _start: ScheduleLimits = dw.json_field("inicio", all=True)  # type: ignore
    _end: ScheduleLimits = dw.json_field("fin", all=True)  # type: ignore
    _rest: ScheduleLimits = dw.json_field("descanso", all=True)  # type: ignore
    _lunch: LunchSchedule = dw.json_field("almuerzo", all=True)  # type: ignore
    _interval: datetime.timedelta = dw.json_field("intervalo", all=True)  # type: ignore pylint: disable=C0301

    @property
    def start(self) -> IScheduleLimitsProvider:
        return self._start

    @property
    def end(self) -> IScheduleLimitsProvider:
        return self._end

    @property
    def rests(self) -> IScheduleLimitsProvider:
        return self._rest

    @property
    def lunch(self) -> ILunchScheduleProvider:
        return self._lunch

    @property
    def interval(self) -> datetime.timedelta:
        return self._interval


@final
@dataclass
class Vehicle(IVehicleProvider):
    """
    Attributes:
        unit_number: El número de la unidad.
        min: La capacidad mínima de pasajeros que puede llevar.
        max: La capacidad máxima de pasajeros que puede llevar.
        available: `True` si la unidad está disponible para realizar
            recorridos, `False` si no lo está.
        route: El id de la ruta que la unidad sigue (string o int).
    """

    _unumber: int = dw.json_field("unidad", all=True)  # type: ignore
    _min: int = dw.json_field("min", all=True)  # type: ignore
    _max: int = dw.json_field("max", all=True)  # type: ignore
    _is_available: bool = dw.json_field("disponible", all=True)  # type: ignore
    _route: str | int = dw.json_field("ruta", all=True)  # type: ignore

    @property
    def unumber(self) -> int:
        return self._unumber

    @property
    def min(self) -> int:
        return self._min

    @property
    def max(self) -> int:
        return self._max

    @property
    def is_available(self) -> bool:
        return self._is_available

    @is_available.setter
    def is_available(self,available: bool):
        self._is_available = available

    @property
    def route_id(self) -> str | int:
        return self._route


@final
@dataclass
class Scores(IScoreProvider):
    """
    Attributes:
        minute_price: Penalización asignada al minuto de espera.
        cap_cost: Penalización por diferencia entre la capacidad máxima
            con la cantidad de personas pronosticadas.
        low_demand_cost: Penalización a despachos realizados
            cuando existe poca demanda.
        zero_demand_cost: Penalización dada a despachos realizados
            cuando no existe demanda.
    """

    _minute_price: float = dw.json_field("precioMinuto", all=True, default=1.0)  # type: ignore pylint: disable=C0301
    _cap_cost: float = dw.json_field("costoCapacidad", all=True, default=1.0)  # type: ignore pylint: disable=C0301
    _low_demand_cost: float = dw.json_field("costoPocosPasajeros", all=True, default=0.5)  # type: ignore pylint: disable=C0301
    _zero_demand_cost: float = dw.json_field("costoVacio", all=True, default=10.0)  # type: ignore pylint: disable=C0301

    @property
    def minute_price(self) -> float:
        return self._minute_price

    @property
    def capacity_cost(self) -> float:
        return self._cap_cost

    @property
    def low_demand_cost(self) -> float:
        return self._low_demand_cost

    @property
    def zero_demand_cost(self) -> float:
        return self._zero_demand_cost


@final
@dataclass
class Params (IParamsProvider):
    """
    Attributes:
        stops: Una lista de paradas, la información de todas las paradas.
        routes: Una lista de rutas, la información de todas las rutas.
        schedule: Los parámetros de la jornada del día.
        scores: Los parámetros para las penalizaciones.
        vehicles: Una lista de vehículos, la información de todas
            las unidades de transporte.
    """

    _stops: list[Stop] = dw.json_field("paradas", all=True)  # type: ignore
    _routes: list[Route] = dw.json_field("rutas", all=True)  # type: ignore
    _schedule: Schedule = dw.json_field("horario", all=True)  # type: ignore
    _scores: Scores = dw.json_field("penalizaciones", all=True)  # type: ignore
    _vehicles: list[Vehicle] = dw.json_field("buses", all=True)  # type: ignore

    @property
    def stops(self) -> tuple[IStopProvider]:
        return tuple(i for i in self._stops)

    @property
    def routes(self) -> tuple[IRouteProvider]:
        return tuple(i for i in self._routes)

    @property
    def schedule(self) -> IScheduleProvider:
        return self._schedule

    @property
    def scores(self) -> IScoreProvider:
        return self._scores

    @property
    def vehicles(self) -> tuple[IVehicleProvider]:
        return tuple(i for i in self._vehicles)


def load_params_from_file(file: str) -> Params:
    """Carga una instancia de `Params` dado una ruta o un archivo.

    Args:
        file: La ubicación del archivo JSON a importar.

    Returns:
        Una instancia de Params con la información dada
        en el archivo JSON.

    Raises:
        ValueError: Si se tiene un formato incorrecto.
        IOError: Si existió un error al leer el archivo.
    """

    with open(file, "r", encoding="utf-8") as f:
        return dw.fromdict(Params, json.load(f))


def save_params_to_file(file: str, params: Params):
    """Exporta los parámetros cargados en memoria a un archivo
    JSON dada su ruta.

    Args:
        file: La ubicación del archivo JSON a exportar.
        params: La instancia de `Params` que será exportada.

    Raises:
        IOError: Si existió un error al escribir el archivo.
    """

    with open(file, "w", encoding="utf-8") as f:
        json.dump(dw.asdict(params), f)
