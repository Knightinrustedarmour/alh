import os

from oemof.solph.processing import results

from mtress import (
    Location,
    MetaModel,
    SolphModel,
    carriers,
    demands,
    technologies,
)
from mtress._helpers import get_flows

os.chdir(os.path.dirname(__file__))

energy_system = MetaModel()

house_1 = Location(name="house_1")
energy_system.add_location(house_1)

# Add carriers
house_1.add(
    carriers.HeatCarrier(
        temperature_levels=[
            10,
            20,
            30,
        ],  # Introduce relevant temperature levels
        reference_temperature=0,  # Energy content is equal to zero
    )
)

# Add technologies
house_1.add(
    technologies.HeatSource(
        name="air_HE",
        reservoir_temperature=25,  # any possible source
        maximum_working_temperature=40,
        minimum_working_temperature=10,
        nominal_power=1e4,
    )
)

# Add demands
house_1.add(
    demands.FixedTemperatureHeating(
        name="heat_demand",
        min_flow_temperature=20,
        return_temperature=10,
        time_series=[50, 50],
    )
)

# Solve the system
solph_representation = SolphModel(
    energy_system,
    timeindex={
        "start": "2022-01-10 00:00:00",
        "end": "2022-01-10 02:00:00",
        "freq": "60T",
    },
)

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=False)
plot.render(outfile="air_heat_exchanger_simple.png")

plot = solph_representation.graph(detail=True)
plot.render(outfile="air_heat_exchanger_detail.png")

solved_model = solph_representation.solve(solve_kwargs={"tee": True})
myresults = results(solved_model)
flows = get_flows(myresults)

plot = solph_representation.graph(detail=True, flow_results=flows)
plot.render(outfile="air_heat_exchanger_results.png")
