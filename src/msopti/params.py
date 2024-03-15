"""Configuraciones y variables para el algoritmo."""

import json
import datetime
from dataclasses import dataclass
import dataclass_wizard as dw


# datatypes
@dataclass
class Stop:
    """Información de una parada.

    Una parada puede ser un punto en varias rutas, para el algoritmo tanto como
    para el modelo, si una parada se encuentra en 2 o más rutas, se consierará
    como si hay 2 o más paradas con el mismo nombre, pero distintos tiempos e
    id.

    Esta clase también contiene el atributo `event_delay`, el cual será por
    defecto 0, y se modificará dinámicamente dependiendo de los eventos que
    registren las unidades.

    También contiene `last_visit`, que registra cuando una parada fue visitada
    por última vez, este se excluye de su representación en JSON debido a que
    es un atributo cuyo objetivo es ser utilizado en tiempo de ejecución.

    Attributes:
        id: Un ID en string o int.
        name: El nombre de la parada.
        time: El tiempo que demora **normalmente** el recorrido desde
            la parada anterior a la parada actual.
        event_delay: El tiempo adicional que tardará el transporte en llegar
            a la parada, (por defecto 0, modificado dinámicamente).
        last_visit: El tiempo en que la parada fue visitada por última vez.
    """

    id: str | int = dw.json_field("id", all=True)  # type: ignore
    name: str = dw.json_field("nombre", all=True)  # type: ignore
    time: datetime.timedelta = dw.json_field("tiempo", all=True)  # type: ignore
    event_delay: datetime.timedelta = dw.json_field("retrasoPorEvento", all=True, default_factory=datetime.timedelta)  # type: ignore pylint: disable=C0301
    visits: list[datetime.datetime] = dw.json_field("visitas", dump=False, default_factory=list)  # type: ignore pylint: disable=C0301

    def visit(self,dt: datetime.datetime):
        self.visits.append(dt)
        self.visits.sort()


@dataclass
class Route:
    """Información de una ruta.

    Una ruta contiene múltiples paradas en un determinado orden, es
    importante que la representación de dichas rutas en esta clase
    mantengan ese mismo orden, no es lo mismo una lista de rutas con
    `[ 0, 1 ]` que una lista de rutas con `[ 1, 0 ]`.

    Attributes:
        id: Un id en string o int.
        stops: Una lista de ids de paradas (strings o ints), indicando las
            paradas que sigue la ruta.
    """

    id: str | int = dw.json_field("id", all=True)  # type: ignore
    stops: list[str | int] = dw.json_field("paradas", all=True)  # type: ignore


@dataclass
class ScheduleLimits:
    """Límite superior e inferior de un horario.

    Contiene mínimo y máximo para distintos horarios los valores son
    representados como distancias de tiempo a partir de las 00:00:00.

    Attributes:
        min: Valor mínimo de tiempo desde las 00:00:00.
        max: Valor máxima de tiempo desde las 00:00:00.
    """

    min: datetime.timedelta = dw.json_field("min", all=True)  # type: ignore
    max: datetime.timedelta = dw.json_field("max", all=True)  # type: ignore


@dataclass
class LunchSchedule:
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

    time: datetime.timedelta = dw.json_field("tiempo", all=True)  # type: ignore
    start: datetime.timedelta = dw.json_field("inicio", all=True)  # type: ignore pylint: disable=C0301
    end: datetime.timedelta = dw.json_field("fin", all=True)  # type: ignore


@dataclass
class Schedule:
    """Descripción de los horarios manejados en un día.

    El inicio y el final de la jornada vienen indicados como `ScheduleLimits`
    y representan la hora mínima a la que debe iniciar/terminar el primer
    recorrido, y la hora máxima a la que debe iniciar/terminal el último
    recorrido.

    Attributes:
        start: Valores mínimos y máximos para el inicio de la jornada.
        end: Valores mínimos y máximos para la finalización de la jornada.
        rest: Valores mínimos y máximos para el tiempo designado para
            descansar entre viaje y viaje.
        lunch: Los horarios del almuerzo.
        interval: Intervalo de tiempo mínimo para reintentar despachar.
    """

    start: ScheduleLimits = dw.json_field("inicio", all=True)  # type: ignore
    end: ScheduleLimits = dw.json_field("fin", all=True)  # type: ignore
    rest: ScheduleLimits = dw.json_field("descanso", all=True)  # type: ignore
    lunch: LunchSchedule = dw.json_field("almuerzo", all=True)  # type: ignore
    interval: datetime.timedelta = dw.json_field("intervalo", all=True)  # type: ignore pylint: disable=C0301


@dataclass
class Vehicle:
    """Información sobre un Vehículo.

    Attributes:
        unit_number: El número de la unidad.
        min: La capacidad mínima de pasajeros que puede llevar.
        max: La capacidad máxima de pasajeros que puede llevar.
        available: `True` si la unidad está disponible para realizar
            recorridos, `False` si no lo está.
        route: El id de la ruta que la unidad sigue (string o int).
    """

    unit_number: int = dw.json_field("unidad", all=True)  # type: ignore
    min: int = dw.json_field("min", all=True)  # type: ignore
    max: int = dw.json_field("max", all=True)  # type: ignore
    available: bool = dw.json_field("disponible", all=True)  # type: ignore
    route: str | int = dw.json_field("ruta", all=True)  # type: ignore


@dataclass
class Scores:
    """Puntuaciones o valores de penalización para cada variable.

    Varios algoritmos requieren de una definición de factores de
    penalización, dependiendo de los valores que estos se escojan
    será el desempeño del algoritmo. Los valores dados por esta
    clase, se multiplicarán a los valores calculados por la
    fórmula, por lo que a mayor sea el valor de acada atributo,
    mayor penalización tendrá el aumento de dicha característica.

    No existe una regla para definir estas puntuaciones, lo que si
    se debe considerar es el valor relativo que estas tendrán con
    respecto a si mismas.

    Cabe recalcar que los algoritmos van a optar por la fórmula con
    el menor resultado posible.

    Attributes:
        minute_price: Penalización asignada al minuto de espera.
        cap_cost: Penalización por diferencia entre la capacidad máxima
            con la cantidad de personas pronosticadas.
        low_demand_cost: Penalización a despachos realizados
            cuando existe poca demanda.
        zero_demand_cost: Penalización dada a despachos realizados
            cuando no existe demanda.
    """

    minute_price: float = dw.json_field("precioMinuto", all=True, default=1.0)  # type: ignore pylint: disable=C0301
    cap_cost: float = dw.json_field("costoCapacidad", all=True, default=1.0)  # type: ignore pylint: disable=C0301
    low_demand_cost: float = dw.json_field("costoPocosPasajeros", all=True, default=0.5)  # type: ignore pylint: disable=C0301
    zero_demand_cost: float = dw.json_field("costoVacio", all=True, default=10.0)  # type: ignore pylint: disable=C0301


@dataclass
class Params:
    """Información de los parámetros y configuraciones en el cual el
    algoritmo va a trabajar.

    Attributes:
        stops: Una lista de paradas, la información de todas las paradas.
        routes: Una lista de rutas, la información de todas las rutas.
        schedule: Los parámetros de la jornada del día.
        scores: Los parámetros para las penalizaciones.
        vehicles: Una lista de vehículos, la información de todas
            las unidades de transporte.
    """

    stops: list[Stop] = dw.json_field("paradas", all=True)  # type: ignore
    routes: list[Route] = dw.json_field("rutas", all=True)  # type: ignore
    schedule: Schedule = dw.json_field("horario", all=True)  # type: ignore
    scores: Scores = dw.json_field("penalizaciones", all=True)  # type: ignore
    vehicles: list[Vehicle] = dw.json_field("buses", all=True)  # type: ignore


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
