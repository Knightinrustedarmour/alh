import os
import pandas as pd
import matplotlib.pyplot as plt
import pytz
#from oemof.solph import EnergySystem, Model
#from oemof.solph import results
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
from mtress._helpers._visualization import render_series

os.chdir(os.path.dirname(__file__))
energy_system = MetaModel()
house_1 = Location(name="Alhambra")
energy_system.add_location(house_1)

house_1.add(carriers.ElectricityCarrier())
house_1.add(technologies.ElectricityGridConnection(working_rate=35))
op_data = pd.read_csv("C:/Users/eshwa/mt/mtress/examples/op_data2.csv")
#file_path = os.path.join(script_dir, "..", "examples", "op_data2.csv")
# op_data = pd.read_csv(file_path)
op_data = op_data.iloc[:1380]
tz_berlin = pytz.timezone("Europe/Berlin")
start_time = pd.Timestamp("2022-08-08 00:00:00+00:00", tz=tz_berlin)
end_time = pd.Timestamp("2022-08-08 23:00:00+00:00", tz=tz_berlin)
date_range = pd.date_range(start=start_time, periods=len(op_data), freq="1T")
op_data.insert(0, "Time", date_range)


house_1.add(demands.Electricity(name="demand0",
                                 time_series=op_data["Load_Watts"]))
house_1.add(technologies.RenewableElectricitySource
            (name= "source2",
             nominal_power=1,
             specific_generation=op_data["Modelled_Energy"], fixed=True))


house_1.add(technologies.BatteryStorage(name="storage1",
                                        nominal_capacity=1,
                                        charging_C_Rate=1,
                                        discharging_C_Rate=1,
                                        charging_efficiency=0.98,
                                        discharging_efficiency=0.95,
                                        loss_rate=0.0,
                                        initial_soc=0.5,
                                        min_soc=0.1))   
try:
    solph_representation = SolphModel(
    energy_system,
    timeindex={
    #     #"start": "2022-08-08 00:00:00+00:00",
    #     "start": "2022-08-08 00:00:00+00:00",
    #     "freq": "1T",
    #     "end": "2022-08-08 23:00:00+00:00",
    #    # "periods": len(op_data) + 1,
    #     #"periods": 993601, 
    #     "tz": "Europe/Berlin",
        "start": start_time,  # Ensuring correct TZ format
        "freq": "1T",
        "end": end_time,  # Ensuring correct TZ format
        "tz": tz_berlin,})

except AssertionError as e:
    print("AssertionError encountered!")
    print(f"Inferred Time Zone: {start_time.tzinfo} (Start) | {end_time.tzinfo} (End)")
    print(f"Passed Time Zone: Europe/Berlin")
    raise

solph_representation.build_solph_model()

plot = solph_representation.graph(detail=True)
plot.render(outfile="alhambra_detail.png")

plot = solph_representation.graph(detail=False)
plot.render(outfile="alhambra_simple.png")

#run.solph.model()

solved_model = solph_representation.solve(solve_kwargs={"tee": True})

# Check if the solver returned a solution
if not solved_model.solutions:
    print("No feasible solution found. Skipping results processing.")
    exit()

# Access solver status and termination condition safely
solver_status = solved_model.solutions[0].solver.status
termination_condition = solved_model.solutions[0].solver.termination_condition
print(f"Solver Status: {solver_status}")
print(f"Termination Condition: {termination_condition}")

# Adjust index length based on actual model output
correct_length = len(solved_model.solutions)  
adjusted_index = pd.RangeIndex(start=0, stop=correct_length, step=1)

# Print active constraints
for constraint in solved_model.component_objects(pyomo.Constraint, active=True):
    print(constraint)

# Check if the solution is empty
if len(solved_model.solutions) == 0:
    print("No feasible solution found. Skipping results processing.")
    exit()

myresults = results(solved_model)
for key in myresults.keys():
    if isinstance(myresults[key], pd.DataFrame):
        if len(myresults[key]) == correct_length:
            myresults[key].index = adjusted_index
flows = get_flows(myresults)

plot.render(outfile="alhambra_results.png")
solved_model.write(
    "alhambra.lp", io_options={"symbolic_solver_labels": True}
)
pv = flows[("Alhambra","source2","source"),("Alhambra","source2","connection")]
load = flows[("Alhambra","ElecticityGridConnection","source_import"),("Alhambra","ElecticityGridConnection","grid_import")]
pv.index = pv.index.tz_convert("Europe/Berlin")
time =pv.index
plt.figure(figsize=(7, 4))
plt.plot(time, pv, label="PV")
plt.legend()
plt.title("PV production")
plt.xlabel("Time (HH:MM)")
plt.ylabel("Watts")
plt.show()
