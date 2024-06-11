"""
Basic working 'electricity' example.
"""

import os
import pandas as pd

from oemof.solph.processing import results

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress._helpers import get_flows
from mtress.physics import HYDROGEN
from mtress.technologies import PEM_ELECTROLYSER

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.Electricity())
house_1.add(technologies.ElectricityGridConnection(working_rate=None, revenue=0.0001))

weather = {
    "ghi": "FILE:../weather.csv:ghi",
    "dhi": "FILE:../weather.csv:dhi",
    "wind_speed": "FILE:../weather.csv:wind_speed",
    "temp_air": "FILE:../weather.csv:temp_air",
    "temp_dew": "FILE:../weather.csv:temp_dew",
    "pressure": "FILE:../weather.csv:pressure",
}


house_1.add(
    technologies.Photovoltaics(
        "pv0",
        (52.729, 8.181),
        nominal_power=8000,
        weather=weather,
        surface_azimuth=180,
        surface_tilt=35,
        fixed=False,
    )
)

house_1.add(
    technologies.Electrolyser(name="Ely", nominal_power=1000, template=PEM_ELECTROLYSER)
)

house_1.add(carriers.GasCarrier(gases={HYDROGEN: [30]}))
house_1.add(carriers.Heat(temperature_levels=[50], reference_temperature=10))
house_1.add(demands.HeatSink(name="Heat-Sink", temperature_levels=30))
house_1.add(
    technologies.GasGridConnection(
        name="H2-Grid",
        working_rate=None,
        gas_type=HYDROGEN,
        grid_pressure=30,
        revenue=7.8,
    )
)
house_2 = Location(name="house_2")
energy_system.add_location(house_2)
house_2.add(carriers.Electricity())
house_2.add(technologies.ElectricityGridConnection(working_rate=0.25, revenue=None))
house_2.add(demands.Electricity(name="demand0", time_series=500))

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 10:00:00",
        "freq": "60T",
        "periods": 10,
        "tz": "Europe/Berlin",
    },
)

# Far from optimal, but currently only works on the existing solph model
house_1.connect(connection=technologies.ElectricityGridConnection, destination=house_2)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="second_location_pv_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="second_location_pv_simple.png")


solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = results(solved_model)
flows = get_flows(myresults)
results = pd.DataFrame(flows)
solved_model.write("electricity_pv.lp", io_options={"symbolic_solver_labels": True})
