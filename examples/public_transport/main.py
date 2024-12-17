import os
import time

import numpy as np

from mnms.simulation import Supervisor
from mnms.demand import CSVDemandManager
from mnms.flow.MFD import Reservoir, MFDFlowMotor
from mnms.log import attach_log_file, LOGLEVEL, set_mnms_logger_level
from mnms.time import Time, Dt
from mnms.io.graph import load_graph, load_odlayer, save_graph, save_odlayer, save_transit_link_odlayer, \
    load_transit_links
from mnms.travel_decision.behavior_and_congestion_decision_model import BehaviorCongestionDecisionModel
from mnms.travel_decision.logit import LogitDecisionModel
from mnms.tools.observer import CSVUserObserver, CSVVehicleObserver
from mnms.generation.layers import generate_bbox_origin_destination_layer
from mnms.mobility_service.personal_vehicle import PersonalMobilityService
from mnms.mobility_service.public_transport import PublicTransportMobilityService
import json

import pandas as pd

indir = "INPUTS"
outdir = "OUTPUTS"

# set_all_mnms_logger_level(LOGLEVEL.WARNING)
set_mnms_logger_level(LOGLEVEL.INFO, ["mnms.simulation"])

#get_logger("mnms.graph.shortest_path").setLevel(LOGLEVEL.WARNING)
attach_log_file(outdir + '/simulation.log')


# 'DESTINATION_R_82604106' 'ORIGIN_E_83202447'

def calculate_V_MFD(acc):
    #V = 10.3*(1-N/57000) # data from fit prop
    V = 0  # data from fit dsty
    N = acc["CAR"]
    if N < 18000:
        V = 11.5 - N * 6 / 18000
    elif N < 55000:
        V = 11.5 - 6 - (N - 18000) * 4.5 / (55000 - 18000)
    elif N < 80000:
        V = 11.5 - 6 - 4.5 - (N - 55000) * 1 / (80000 - 55000)
    #V = 11.5*(1-N/60000)
    V = max(V, 0.001)  # min speed to avoid gridlock
    V_TRAM_BUS = 0.7 * V
    return {"CAR": V, "METRO": 17, "BUS": V_TRAM_BUS, "TRAM": V_TRAM_BUS}


def load_capacity_info(capacity_file):
    print("Loading capacity info from {}".format(capacity_file))
    capacity_info = {}
    with open(capacity_file, 'r') as f:
        pt_network = json.load(f)
        for i in range(len(pt_network['LAYERS'])):
            layer = pt_network['LAYERS'][i]
            layer_id = layer['ID']
            if 'METRO' in layer_id or 'BUS' in layer_id or 'TRAM' in layer_id:
                for k in range(len(layer['LINES'])):
                    veh = layer['LINES'][k]['ID']
                    capacity_info[veh] = layer['LINES'][k]['CAPACITY']
    return capacity_info


def force_public_transport(demand_file):
    print('Forcing public transport from {}'.format(demand_file))
    demand_data = pd.read_csv(demand_file, sep=';')
    print('N queries:', len(demand_data), 'N users:', len(np.unique(demand_data['ID'])))
    demand_data['MOBILITY SERVICES'] = 'TRAM'
    demand_data.to_csv(demand_file, sep=';', index=False)


if __name__ == '__main__':
    NX = 100
    NY = 100
    #DIST_CONNECTION = 1e2

    mmgraph = load_graph(indir + "/lyon_network_gtfs_mod.json")
    start_time = time.time()
    odlayer = generate_bbox_origin_destination_layer(mmgraph.roads, NX, NY)
    mmgraph.odlayer = odlayer
    end_time = time.time()
    print('OD LAYER CREATION', end_time - start_time, 's')

    ##
    # start_time = time.time()
    mmgraph.add_origin_destination_layer(odlayer)
    # mmgraph.connect_origindestination_layers(500, 1000)
    # end_time = time.time()
    # print('MMGRAPH LAYER CREATION', end_time - start_time, 's')

    if not os.path.exists(indir + f"/transit_link_{NX}_{NY}_{500}_grid.json"):
        mmgraph.connect_origindestination_layers(500, 1000)
        save_transit_link_odlayer(mmgraph, indir + f"/transit_link_{NX}_{NY}_{500}_grid.json")
    else:
        start_time = time.time()
        load_transit_links(mmgraph, indir + f"/transit_link_{NX}_{NY}_{500}_grid.json")
        end_time = time.time()
        print('MMGRAPH LAYER UPLOADING', end_time - start_time, 's')

    personal_car = PersonalMobilityService()
    personal_car.attach_vehicle_observer(CSVVehicleObserver(outdir + "/veh.csv"))
    mmgraph.layers["CAR"].add_mobility_service(personal_car)

    capacity_info = load_capacity_info(indir + "/lyon_network_gtfs_mod.json")

    bus_service = PublicTransportMobilityService("BUS")
    bus_service.attach_vehicle_observer(CSVVehicleObserver(outdir + "/veh.csv"))
    mmgraph.layers["BUSLayer"].add_mobility_service(bus_service)

    tram_service = PublicTransportMobilityService("TRAM")
    tram_service.attach_vehicle_observer(CSVVehicleObserver(outdir + "/veh.csv"))
    mmgraph.layers["TRAMLayer"].add_mobility_service(tram_service)

    metro_service = PublicTransportMobilityService("METRO")
    metro_service.attach_vehicle_observer(CSVVehicleObserver(outdir + "/veh.csv"))
    mmgraph.layers["METROLayer"].add_mobility_service(metro_service)

    demand_file_name = indir + "/test_demandes.csv"
    force_public_transport(demand_file_name)
    demand = CSVDemandManager(demand_file_name)
    demand.add_user_observer(CSVUserObserver(outdir + "/user.csv"), user_ids="all")

    flow_motor = MFDFlowMotor(outfile=outdir + "/flow.csv")
    flow_motor.add_reservoir(Reservoir(mmgraph.roads.zones["RES"], ["CAR"], calculate_V_MFD))

    travel_decision = LogitDecisionModel(mmgraph, outfile=outdir + "/path.csv")
    # travel_decision = BehaviorCongestionDecisionModel(mmgraph, outfile=outdir + "/path.csv", alpha=0, beta=0)

    supervisor = Supervisor(graph=mmgraph,
                            flow_motor=flow_motor,
                            demand=demand,
                            decision_model=travel_decision,
                            outfile=outdir + "/travel_time_link.csv")

    start = time.time()
    # supervisor.run(Time('8:18:00'), Time('9:15:00'), Dt(seconds=30), 10)
    supervisor.run(Time('8:15:00'), Time('9:00:00'), Dt(seconds=30), 10)
    end = time.time()
    print(f'SIMULATION COMPLETED IN {end-start} s')


    ''''
    "STOPS": [
            "TRAM_T5_DIR1_EurexpoEntreePrinc",
            "TRAM_T5_DIR1_ParcduChene",
            "TRAM_T5_DIR1_LyceeJPSartre",
            "TRAM_T5_DIR1_DeTassignyCurial",
            "TRAM_T5_DIR1_LesAlizes",
            "TRAM_T5_DIR1_BronHoteldeVille",
            "TRAM_T5_DIR1_BoutasseCRousset",
            "TRAM_T5_DIR1_EssartsIris",
            "TRAM_T5_DIR1_Desgenettes",
            "TRAM_T5_DIR1_AmbroisePare",
            "TRAM_T5_DIR1_GrangeBlanche"
          ],
          "TIMETABLE": [
            "07:51:00",
            "08:24:00",
            "08:51:00",
            "09:18:00",
            "09:45:00",
            "10:12:00",
            "10:39:00",
            "11:07:00",
            "11:21:00",
            "11:35:00",
            "11:50:00",
            "12:05:00",
            "12:20:00",
            "12:35:00",
            "12:50:00",
            "13:05:00",
            "13:20:00",
            "13:35:00",
            "13:50:00",
            "14:05:00",
            "14:20:00",
            "14:35:00",
            "14:50:00",
            "15:05:00",
            "15:20:00",
            "15:35:00",
            "15:50:00",
            "16:05:00",
            "16:20:00",
            "16:34:00",
            "16:55:00",
            "17:22:00",
            "18:22:00",
            "18:57:00",
            "19:11:00",
            "19:26:00",
            "19:40:00",
            "19:55:00",
            "20:10:00",
            "20:35:00",
            "21:00:00",
            "21:25:00"
          ],
          
          
          
          "TRAM_T5_DIR1_EurexpoEntreePrinc": {
        "id": "TRAM_T5_DIR1_EurexpoEntreePrinc",
        "section": "TRAM_T5_DIR1_0_1",
        "relative_position": 0.0,
        "absolute_position": [
          651559.9412157426,
          5066124.587525388
        ]
      },
      "TRAM_T5_DIR1_ParcduChene": {
        "id": "TRAM_T5_DIR1_ParcduChene",
        "section": "TRAM_T5_DIR1_1_2",
        "relative_position": 0.0,
        "absolute_position": [
          649880.8936320535,
          5066860.9618538
        ]
      },
      "TRAM_T5_DIR1_LyceeJPSartre": {
        "id": "TRAM_T5_DIR1_LyceeJPSartre",
        "section": "TRAM_T5_DIR1_2_3",
        "relative_position": 0.0,
        "absolute_position": [
          649536.627479743,
          5066740.401696204
        ]
      },
      "TRAM_T5_DIR1_DeTassignyCurial": {
        "id": "TRAM_T5_DIR1_DeTassignyCurial",
        "section": "TRAM_T5_DIR1_3_4",
        "relative_position": 0.0,
        "absolute_position": [
          649140.4680528969,
          5066478.55043876
        ]
      },
      "TRAM_T5_DIR1_LesAlizes": {
        "id": "TRAM_T5_DIR1_LesAlizes",
        "section": "TRAM_T5_DIR1_4_5",
        "relative_position": 0.0,
        "absolute_position": [
          648978.9519313243,
          5066006.681442318
        ]
      },
      "TRAM_T5_DIR1_BronHoteldeVille": {
        "id": "TRAM_T5_DIR1_BronHoteldeVille",
        "section": "TRAM_T5_DIR1_5_6",
        "relative_position": 0.0,
        "absolute_position": [
          648532.8129872896,
          5066205.004377294
        ]
      },
      "TRAM_T5_DIR1_BoutasseCRousset": {
        "id": "TRAM_T5_DIR1_BoutasseCRousset",
        "section": "TRAM_T5_DIR1_6_7",
        "relative_position": 0.0,
        "absolute_position": [
          648171.6794905056,
          5066365.362887161
        ]
      },
      "TRAM_T5_DIR1_EssartsIris": {
        "id": "TRAM_T5_DIR1_EssartsIris",
        "section": "TRAM_T5_DIR1_7_8",
        "relative_position": 0.0,
        "absolute_position": [
          647672.3883533132,
          5066608.05638861
        ]
      },
      "TRAM_T5_DIR1_Desgenettes": {
        "id": "TRAM_T5_DIR1_Desgenettes",
        "section": "TRAM_T5_DIR1_8_9",
        "relative_position": 0.0,
        "absolute_position": [
          647289.2826723342,
          5066777.947201837
        ]
      },
      "TRAM_T5_DIR1_AmbroisePare": {
        "id": "TRAM_T5_DIR1_AmbroisePare",
        "section": "TRAM_T5_DIR1_9_10",
        "relative_position": 0.0,
        "absolute_position": [
          646555.6395575586,
          5067059.648079293
        ]
      },
      "TRAM_T5_DIR1_GrangeBlanche": {
        "id": "TRAM_T5_DIR1_GrangeBlanche",
        "section": "TRAM_T5_DIR1_9_10",
        "relative_position": 1.0,
        "absolute_position": [
          646207.7669526552,
          5067157.066273123
        ]
      },
      
TRAM_T5_DIR1_EurexpoEntreePrinc	(651559.9412157426, 5066124.587525388)
TRAM_T5_DIR1_ParcduChene	(649880.8936320535, 5066860.9618538)
TRAM_T5_DIR1_LyceeJPSartre	(649536.627479743, 5066740.401696204)
TRAM_T5_DIR1_DeTassignyCurial	(649140.4680528969, 5066478.55043876)
TRAM_T5_DIR1_LesAlizes	(648978.9519313243, 5066006.681442318)
TRAM_T5_DIR1_BronHoteldeVille	(648532.8129872896, 5066205.004377294)
TRAM_T5_DIR1_BoutasseCRousset	(648171.6794905056, 5066365.362887161)
TRAM_T5_DIR1_EssartsIris	(647672.3883533132, 5066608.05638861)
TRAM_T5_DIR1_Desgenettes	(647289.2826723342, 5066777.947201837)
TRAM_T5_DIR1_AmbroisePare	(646555.6395575586, 5067059.648079293)
TRAM_T5_DIR1_GrangeBlanche	(646207.7669526552, 5067157.066273123)
'''
