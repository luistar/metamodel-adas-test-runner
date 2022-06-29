import json
import time
import click
import numpy as np
import pandas
import matplotlib.pyplot as plt
import seaborn as sns
from math import dist
from beamngpy import BeamNGpy, Scenario, Road, Vehicle, StaticObject
from beamngpy.sensors import Electrics

sns.set()


def generate_roads(scenario, test_scenario):
    road_topology = pandas.read_csv(f'scenarios/{test_scenario}.csv')
    road_topology = road_topology[road_topology["Tipo"] == "DistrictRoad"]

    the_road = Road('tig_road_rubber_sticky', rid='main_road')
    road_nodes = []
    for index, node in road_topology.iterrows():
        road_nodes.append(
            (round(node['X']), -1 * round(node['Y']), node['Z'], node['Width'])
        )
    # print(road_nodes)
    the_road.nodes.extend(road_nodes)
    scenario.add_road(the_road)

    # create a checkpoint at the end of the road
    scenario.add_checkpoints(
        [(road_topology.iloc[-1]['X'], -1*road_topology.iloc[-1]['Y'], -28)],  # pos
        [(1, 1, 1)],  # scale
        ['end_of_road']  # id
    )
    return the_road


def generate_ego_vehicle(scenario, test_scenario):
    ego_vehicles = pandas.read_csv(f'scenarios/{test_scenario}.csv')
    ego_vehicles = ego_vehicles[ego_vehicles["Tipo"] == "EgoVehicle"]

    # assume one ego vehicle
    position_x = ego_vehicles.iloc[0]['X']
    position_y = -1 * ego_vehicles.iloc[0]['Y']  # flip on x axis
    # ETK800 is a more traditional model
    vehicle = Vehicle('ego_vehicle', model='ETK800', licence='WASA', color='Red')

    # Create an Electrics sensor and attach it to the vehicle
    electrics = Electrics()
    vehicle.attach_sensor('electrics', electrics)

    # Add it to our scenario at this position and rotation
    scenario.add_vehicle(vehicle, pos=(position_x, position_y, -28), rot=(0, 0, 270))
    return vehicle


def generate_static_objects(scenario, test_scenario):
    trees = pandas.read_csv(f'scenarios/{test_scenario}.csv')
    trees = trees[trees["Tipo"] == "Tree"]
    for index, t in trees.iterrows():
        tree = StaticObject(name=f'tree_{index}',
                            pos=(t['X'], t['Y']*-1, -28),
                            rot=(0, 0, -80), scale=(1, 1, 1),
                            shape='/levels/west_coast_usa/art/shapes/trees/trees_oak/oak_a.dae')
        scenario.add_object(tree)


def generate_vehicles(scenario, test_scenario):
    cars = pandas.read_csv(f'scenarios/{test_scenario}.csv')
    cars = cars[cars["Tipo"] == "Car"]
    vehicles = []
    for index, c in cars.iterrows():
        vehicle = Vehicle(f'car_{index}', model='ETK800', licence=f'CAR{index}', color='White')
        scenario.add_vehicle(vehicle, pos=(c['X'], c['Y']*-1, -28), rot=(0, 0, 90))
        vehicles.append(vehicle)
    return vehicles


def plot_scenario(test_scenario):
    road_topology = pandas.read_csv(f'scenarios/{test_scenario}.csv')
    road_topology = road_topology[road_topology["Tipo"] == "DistrictRoad"]

    road_topology.plot.scatter(x='X', y='Y', marker='')
    road_topology.plot.line(x='X', y='Y', marker='')
    plt.gca().invert_yaxis()
    plt.show()
    pass


@click.command()
@click.option('--beamng-home', required=True, type=click.Path(exists=True),
              help="Customize BeamNG executor by specifying the home of the simulator.")
@click.option('--beamng-user', required=True, type=click.Path(exists=True),
              help="Customize BeamNG executor by specifying the location of the folder "
                   "where levels, props, and other BeamNG-related data will be copied."
                   "** Use this to avoid spaces in URL/PATHS! **")
@click.option('--test-scenario', required=True, help="Name of the scenario")
def run(beamng_home, beamng_user, test_scenario):

    # plot input scenario
    plot_scenario(test_scenario)

    # create beamngpy instance
    beamng = BeamNGpy('localhost', 5000, home=beamng_home, user=beamng_user)
    bng = beamng.open(launch=True)

    # create base scenario
    scenario = Scenario('tig', test_scenario)

    # generate roads according to the test description
    the_road = generate_roads(scenario, test_scenario)

    # generate static objects
    generate_static_objects(scenario, test_scenario)

    # generate other vehicles
    vehicles = generate_vehicles(scenario, test_scenario)

    # generate the ego vehicle
    ego_vehicle = generate_ego_vehicle(scenario, test_scenario)

    scenario.make(bng)

    try:
        bng.load_scenario(scenario)
        bng.start_scenario()
        bng.switch_vehicle(ego_vehicle)
        #Set behaviour for the other vehicles
        for v in vehicles:
            v.ai_set_mode('span')
            v.ai_drive_in_lane(True)
        # Set behaviour for the ego vehicle
        ego_vehicle.ai_set_mode('manual')
        ego_vehicle.ai_drive_in_lane(True)
        ego_vehicle.ai_set_waypoint('end_of_road')
        last_node = the_road.nodes[-1]

        ego_vehicle.update_vehicle()
        beamng.poll_sensors(ego_vehicle)

        current_position = ego_vehicle.state['pos']

        positions = list()
        directions = list()
        wheel_speeds = list()
        throttles = list()
        brakes = list()

        current_xy = (current_position[0], current_position[1])
        goal_xy = (last_node[0], last_node[1])

        sensors_data = []

        while dist(current_xy, goal_xy) > 5:

            time.sleep(0.1)
            # print(dist(current_xy, goal_xy))
            ego_vehicle.update_vehicle()
            sensors = beamng.poll_sensors(ego_vehicle)
            sensors_data.append(sensors)

            current_position = ego_vehicle.state['pos']
            current_xy = (current_position[0], current_position[1])
            positions.append(current_position)
            directions.append(ego_vehicle.state['dir'])
            # print(sensors['electrics'])
            wheel_speeds.append(sensors['electrics']['wheelspeed'])
            throttles.append(sensors['electrics']['throttle'])
            brakes.append(sensors['electrics']['brake'])
    finally:
        print("Simulation done")
        bng.close()
        print("Saving output")
        with open(f"output/{test_scenario}.json", "w+") as output_file:
            json.dump(sensors_data, output_file)

    plt.plot(throttles, 'b-', label='Throttle')
    plt.plot(brakes, 'r-', label='Brake')
    plt.show()
    plt.clf()

    x = [p[0] for p in positions]
    y = [p[1] for p in positions]
    plt.plot(x, y, '.')
    plt.axis('square')
    plt.show()
    plt.clf()

    angles = [np.arctan2(d[1], d[0]) for d in directions]
    r = wheel_speeds  # We simply use the speed as the radius in the radial plot
    plt.subplot(111, projection='polar')
    plt.scatter(angles, r)
    plt.show()


if __name__ == '__main__':
    run()
