"""
.. module:: road_definition
    :platform: Windows
    :synopsis: Example code making a scenario that defines new roads to drive
               on.
.. moduleauthor:: Marc Müller <mmueller@beamng.gmbh>
"""

from beamngpy import BeamNGpy, Scenario, Road, Vehicle, setup_logging, StaticObject, ProceduralRing


def main():
    beamng = BeamNGpy('localhost', 64256, home="D:/BeamNG/", user="D:/BeamNG_user/")
    bng = beamng.open(launch=True)

    scenario = Scenario('tig', 'First scenario with dynamically generated road')

    # road_a = Road('track_editor_C_center', rid='circle_road', looped=True)
    # nodes = [
    #     (-25, 300, 0, 5),
    #     (25, 300, 0, 6),
    #     (25, 350, 0, 4),
    #     (-25, 350, 0, 5),
    # ]
    # road_a.nodes.extend(nodes)
    # scenario.add_road(road_a)

    road_b = Road('tig_road_rubber_sticky', rid='center_road')
    nodes = [
        (0, 0, 0, 5),
        (0, 50, 0, 5),
        (50, 50, 0, 5),
        (60, 100, 0, 5),
        (40, 200, 0, 5),
        (50, 375, 0, 5),
    ]
    road_b.nodes.extend(nodes)
    scenario.add_road(road_b)

    # load a static ramp
    ramp = StaticObject(name='ramp', pos=(50, 372, -28), rot=(0, 0, -2), scale=(0.5, 0.5, 0.5),
                        shape='/levels/west_coast_usa/art/shapes/objects/ramp_massive.dae')
    scenario.add_object(ramp)

    # add a static procedurally generated ring
    ring = ProceduralRing(name='ring', pos=(46, 470, 28), rot=(0, 0, 90), radius=5, thickness=2.5)
    scenario.add_procedural_mesh(ring)

    # load a static tree
    tree = StaticObject(name='tree', pos=(70, 70, -28), rot=(0, 0, -2), scale=(1, 1, 1),
                        shape='/levels/west_coast_usa/art/shapes/trees/trees_oak/oak_a.dae')
    scenario.add_object(tree)


    # ETK800 is a more traditional model
    vehicle = Vehicle('ego_vehicle', model='pigeon', licence='UNINA', color='Green')

    # Add it to our scenario at this position and rotation
    #scenario.add_vehicle(vehicle, pos=(50, 375, -28), rot=None, rot_quat=(0, 0, 0.3826834, 0.9238795))
    scenario.add_vehicle(vehicle, pos=(0, 0, -28), rot=(0, 0, 180))

    scenario.make(bng)

    try:
        bng.load_scenario(scenario)
        bng.start_scenario()
        input('Press enter when done...')
    finally:
        bng.close()

if __name__ == '__main__':
    main()