"""Simple example to illustrate heat production from resistive heater"""

import os

from oemof.solph.processing import results

from mtress import Location, MetaModel, SolphModel, carriers, demands, technologies
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

house_1.add(carriers.Electricity())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))

house_1.add(
    demands.Electricity(
        name="electricity demand",
        time_series=[9, 13],
    )
)

house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[20, 30],
        reference_temperature=10,
    )
)
house_1.add(
    technologies.ResistiveHeater(
        name="Resistive_Heater",
        nominal_power=20,
        maximum_temperature=30,
    )
)
house_1.add(
    demands.FixedTemperatureHeat(
        name="heating",
        flow_temperature=30,
        return_temperature=20,
        time_series=[2, 10],
    )
)

solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2021-07-10 00:00:00",
        "end": "2021-07-10 02:00:00",
        "freq": "60T",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="heat_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="heat_simple.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = results(solved_model)
flows = get_flows(myresults)

solved_model.write("heat.lp", io_options={"symbolic_solver_labels": True})
