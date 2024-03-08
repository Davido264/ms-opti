"""Ejecutar el módulo"""
import os
import typing
from msopti import params
from msopti.algorithm import annealing, formula, interfaces
import pandas as pd
import datetime
import asyncio
import dataclass_wizard as dw

# Globals
ROUTE = 30
P = params.load_params_from_file(os.environ["PARAMS_PATH"])
DF = pd.read_csv(os.environ["DATASET_TEST_PATH"])

def available(i: params.Vehicle, start_point: int) -> bool:
    return i.available and i.route == ROUTE and i.start_point == start_point

async def run(start: int, stop: int):
    units = [i for i in P.vehicles if available(i,start)]
    route = next(i for i in P.routes if i.id == ROUTE)
    stops = [i for i in P.stops if i.id in route.stops]

    cap_score = P.scores.cap_cost
    time_score = P.scores.minute_price
    low_demand_score = P.scores.low_demand_cost
    zero_demand_score = P.scores.zero_demand_cost
    interval = P.schedule.interval

    today = datetime.datetime(2024,3,23)
    forecast = typing.cast(pd.DataFrame,DF[DF["stop_id"].isin(route.stops)])
    forecast["timespan"] = pd.DatetimeIndex(DF["timespan"])
    forecast.set_index(keys="timespan",inplace=True)
    initial_time = today + P.schedule.start.min
    final_time = today + P.schedule.start.max
    forecast = forecast.between_time(initial_time.time(),final_time.time())
    time_max = (final_time - initial_time) / len(units)

    solutions: list[interfaces.Solution] = []
    while len(units) != 0:
        f = formula.gererate_formula(forecast,[start,stop],stops,P.scores,today)
        an2 = annealing.AnnealSolver(
            f,
            time_score,
            cap_score,
            low_demand_score,
            zero_demand_score,
            initial_time,
            time_max,
            interval,
            units,
            stops,
            start
        )
        solution = an2.solve()
        solutions.append(solution)
        unit = next(u for u in units if u.unit_number == solution.unit.unit_number)
        unit.available = False
        units = [i for i in P.vehicles if available(i,start)]
        initial_time += datetime.timedelta(minutes=solution.delay) + P.schedule.interval

        # TODO: Mover esta implementación a solve_multi y considerar los cambios y reordenamiento de las rutas
        for i,sto in enumerate(solution.planification):
            last_time = datetime.datetime(
                year=initial_time.year,
                month=initial_time.month,
                day=initial_time.day,
                hour=sto.time.hour,
                minute=sto.time.minute
            )
            stops[i].last_visit = last_time

    return solutions


async def main():
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(run(0,5))
        task2 = tg.create_task(run(5,0))

    solutions1 = task1.result()
    solutions2 = task2.result()
    df1 = pd.concat([i.to_dataframe() for i in solutions1])
    df2 = pd.concat([i.to_dataframe() for i in solutions2])

    master_df = pd.concat([df1,df2])

    print("===  Planification  ==")
    print("== Configuraciones ===")
    print(f"    Se intentará despachar como mínimo cada {P.schedule.interval}")
    # TODO: configuración para los puntos de salida dentro de params.json
    print(f"    Los puntos de partida serán las paradas:  {P.stops[0].name} y {P.stops[5].name}")
    print("\n")
    print("== Unidades despachadas (en orden) ===")

    for x in [0,5]:
        print(f"Stop: {dw.asdict(P.stops[x], exclude=('time', 'event_delay', 'last_visit'))}")
        sol = solutions1 if x == 0 else solutions2
        for i in sol:
            print(f"    {dw.asdict(i.unit, exclude=('available','start_point','route'))}")
            print(f"         {[j.time.isoformat() for j in i.planification]}")
            print(f"         Esperado {i.delay} minutos antes de despachar")
            print("\n\n")

    print("View results on testing.csv")
    master_df.to_csv("testing.csv")

asyncio.run(main())
