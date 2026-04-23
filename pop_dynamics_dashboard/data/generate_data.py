"""
generate_data.py
Generates county-level Texas data for the Population Dynamics Map.

Sources:
  - Population: 2020 Decennial Census + TDC 2022 County Projections growth rates
  - Water demand: TWDB 2022 State Water Plan (regional averages, scaled by population)
  - Electricity demand: ERCOT 2024 LTDEF by weather zone, apportioned to counties
  - New load: existing gen_dashboard/data/projects.csv (by county)

Run once from this directory:
    python generate_data.py

Outputs:
    merged_county_data.csv   – one row per county, all metrics
    population_projections.csv
    water_demand.csv
    electricity_demand.csv
"""

import json
import re
import os
import sys
import csv
import math

# ─────────────────────────────────────────────────────────────────────────────
# 1. All 254 Texas counties
#    Fields: fips, name, pop_2020, lat, lon, ercot_zone, twdb_region
#    Population from 2020 Decennial Census P1 table.
#    Lat/Lon = approx county seat centroid (WGS84).
#    ERCOT weather zones (8 used in LTDEF):
#      NCENT, NORTH, WEST, FWEST, SOUTH, SCENT, COAST, EAST
#    TWDB water planning regions: A-P (16 regions)
# ─────────────────────────────────────────────────────────────────────────────

COUNTIES = [
    # FIPS, Name, Pop2020, Lat, Lon, ERCOT_Zone, TWDB_Region
    ("48001","Anderson",57922,31.82,-95.65,"EAST","D"),
    ("48003","Andrews",18705,32.31,-102.64,"WEST","F"),
    ("48005","Angelina",86715,31.39,-94.61,"EAST","D"),
    ("48007","Aransas",26065,28.07,-97.04,"SOUTH","N"),
    ("48009","Archer",8786,33.62,-98.68,"NORTH","B"),
    ("48011","Armstrong",1887,34.97,-101.36,"WEST","B"),
    ("48013","Atascosa",51153,28.89,-98.53,"SCENT","L"),
    ("48015","Austin",30167,29.88,-96.27,"COAST","K"),
    ("48017","Bailey",6904,34.07,-102.83,"WEST","O"),
    ("48019","Bandera",23112,29.73,-99.24,"SCENT","L"),
    ("48021","Bastrop",96835,30.10,-97.31,"SCENT","K"),
    ("48023","Baylor",3530,33.62,-99.22,"NORTH","B"),
    ("48025","Bee",32565,28.42,-97.74,"SOUTH","N"),
    ("48027","Bell",362924,31.04,-97.47,"SCENT","G"),
    ("48029","Bexar",2009324,29.45,-98.52,"SOUTH","L"),
    ("48031","Blanco",13751,30.26,-98.42,"SCENT","J"),
    ("48033","Borden",663,32.74,-101.43,"WEST","F"),
    ("48035","Bosque",18685,31.90,-97.64,"NORTH","G"),
    ("48037","Bowie",93245,33.44,-94.42,"EAST","D"),
    ("48039","Brazoria",372031,29.17,-95.44,"COAST","H"),
    ("48041","Brazos",229211,30.66,-96.30,"EAST","K"),
    ("48043","Brewster",9203,29.85,-103.25,"FWEST","F"),
    ("48045","Briscoe",1546,34.53,-100.55,"WEST","B"),
    ("48047","Brooks",7093,27.04,-98.22,"SOUTH","N"),
    ("48049","Brown",37864,31.72,-99.01,"NCENT","F"),
    ("48051","Burleson",18443,30.49,-96.62,"EAST","K"),
    ("48053","Burnet",48155,30.79,-98.22,"SCENT","J"),
    ("48055","Caldwell",45883,29.83,-97.62,"SCENT","K"),
    ("48057","Calhoun",21290,28.44,-96.61,"COAST","N"),
    ("48059","Callahan",14519,32.30,-99.37,"NCENT","F"),
    ("48061","Cameron",423163,26.17,-97.65,"SOUTH","M"),
    ("48063","Camp",13094,32.97,-94.98,"EAST","D"),
    ("48065","Carson",5926,35.40,-101.35,"WEST","B"),
    ("48067","Cass",30042,33.08,-94.35,"EAST","D"),
    ("48069","Castro",7530,34.53,-102.26,"WEST","O"),
    ("48071","Chambers",46805,29.71,-94.66,"COAST","H"),
    ("48073","Cherokee",52646,31.84,-95.16,"EAST","D"),
    ("48075","Childress",6664,34.53,-100.21,"WEST","B"),
    ("48077","Clay",10471,33.78,-98.21,"NORTH","B"),
    ("48079","Cochran",2547,33.60,-102.83,"WEST","O"),
    ("48081","Coke",3387,31.88,-100.53,"WEST","F"),
    ("48083","Coleman",8175,31.82,-99.43,"NCENT","F"),
    ("48085","Collin",1064465,33.19,-96.57,"NCENT","C"),
    ("48087","Collingsworth",2680,34.97,-100.27,"WEST","B"),
    ("48089","Colorado",21493,29.62,-96.52,"COAST","K"),
    ("48091","Comal",178511,29.80,-98.27,"SCENT","L"),
    ("48093","Comanche",13635,31.95,-98.55,"NCENT","G"),
    ("48095","Concho",2726,31.32,-99.86,"NCENT","F"),
    ("48097","Cooke",42558,33.64,-97.21,"NORTH","B"),
    ("48099","Coryell",76192,31.39,-97.80,"SCENT","G"),
    ("48101","Cottle",1398,34.08,-100.27,"WEST","B"),
    ("48103","Crane",4839,31.42,-102.35,"FWEST","F"),
    ("48105","Crockett",3416,30.72,-101.21,"FWEST","F"),
    ("48107","Crosby",5737,33.61,-101.30,"WEST","O"),
    ("48109","Culberson",2171,31.45,-104.52,"FWEST","F"),
    ("48111","Dallam",7341,36.28,-102.60,"WEST","A"),
    ("48113","Dallas",2613539,32.77,-96.80,"NCENT","C"),
    ("48115","Dawson",12833,32.74,-101.95,"WEST","F"),
    ("48117","Deaf Smith",18561,34.97,-102.60,"WEST","A"),
    ("48119","Delta",5331,33.39,-95.67,"NORTH","D"),
    ("48121","Denton",906422,33.21,-97.12,"NCENT","C"),
    ("48123","DeWitt",20013,29.09,-97.35,"SOUTH","N"),
    ("48125","Dickens",2216,33.62,-100.79,"WEST","O"),
    ("48127","Dimmit",9996,28.42,-99.75,"SOUTH","L"),
    ("48129","Donley",3278,34.97,-100.81,"WEST","B"),
    ("48131","Duval",11157,27.68,-98.53,"SOUTH","N"),
    ("48133","Eastland",18583,32.40,-98.83,"NCENT","F"),
    ("48135","Ector",165472,31.87,-102.55,"WEST","F"),
    ("48137","Edwards",1932,29.98,-100.30,"SOUTH","J"),
    ("48139","Ellis",185748,32.35,-96.80,"NCENT","C"),
    ("48141","El Paso",865657,31.77,-106.42,"FWEST","E"),
    ("48143","Erath",42698,32.24,-98.22,"NORTH","G"),
    ("48145","Falls",17297,31.25,-96.93,"EAST","G"),
    ("48147","Fannin",35514,33.59,-96.11,"NORTH","D"),
    ("48149","Fayette",25346,29.88,-96.92,"COAST","K"),
    ("48151","Fisher",3830,32.74,-100.40,"WEST","F"),
    ("48153","Floyd",5767,33.97,-101.30,"WEST","O"),
    ("48155","Foard",1155,33.98,-99.78,"NORTH","B"),
    ("48157","Fort Bend",822779,29.53,-95.77,"COAST","H"),
    ("48159","Franklin",10679,33.18,-95.22,"EAST","D"),
    ("48161","Freestone",19816,31.70,-96.14,"EAST","G"),
    ("48163","Frio",20306,28.87,-99.11,"SOUTH","L"),
    ("48165","Gaines",21492,32.74,-102.64,"WEST","F"),
    ("48167","Galveston",342139,29.35,-94.90,"COAST","H"),
    ("48169","Garza",6229,33.18,-101.30,"WEST","O"),
    ("48171","Gillespie",26208,30.32,-98.93,"SCENT","J"),
    ("48173","Glasscock",1572,31.87,-101.52,"WEST","F"),
    ("48175","Goliad",7531,28.66,-97.39,"SOUTH","N"),
    ("48177","Gonzales",20837,29.50,-97.45,"SCENT","N"),
    ("48179","Gray",21886,35.40,-100.81,"WEST","B"),
    ("48181","Grayson",136212,33.62,-96.68,"NORTH","D"),
    ("48183","Gregg",123945,32.47,-94.82,"EAST","D"),
    ("48185","Grimes",28880,30.55,-95.98,"EAST","K"),
    ("48187","Guadalupe",174680,29.57,-97.94,"SCENT","L"),
    ("48189","Hale",33406,34.07,-101.82,"WEST","O"),
    ("48191","Hall",2964,34.53,-100.68,"WEST","B"),
    ("48193","Hamilton",8461,31.70,-98.12,"NORTH","G"),
    ("48195","Hansford",5399,36.28,-101.36,"WEST","A"),
    ("48197","Hardeman",3933,34.29,-99.75,"NORTH","B"),
    ("48199","Hardin",57602,30.32,-94.38,"EAST","I"),
    ("48201","Harris",4731145,29.85,-95.40,"COAST","H"),
    ("48203","Harrison",67906,32.55,-94.37,"EAST","D"),
    ("48205","Hartley",5576,35.84,-102.60,"WEST","A"),
    ("48207","Haskell",5658,33.17,-99.73,"NORTH","B"),
    ("48209","Hays",246521,30.06,-98.03,"SCENT","K"),
    ("48211","Hemphill",4018,35.84,-100.27,"WEST","B"),
    ("48213","Henderson",82737,32.21,-95.85,"EAST","D"),
    ("48215","Hidalgo",870781,26.40,-98.18,"SOUTH","M"),
    ("48217","Hill",35972,31.99,-97.13,"NORTH","G"),
    ("48219","Hockley",23021,33.61,-102.34,"WEST","O"),
    ("48221","Hood",69468,32.43,-97.83,"NORTH","G"),
    ("48223","Hopkins",37084,33.14,-95.57,"EAST","D"),
    ("48225","Houston",23225,31.33,-95.42,"EAST","D"),
    ("48227","Howard",36664,32.30,-101.44,"WEST","F"),
    ("48229","Hudspeth",3476,31.41,-105.37,"FWEST","F"),
    ("48231","Hunt",98594,33.13,-96.08,"NORTH","D"),
    ("48233","Hutchinson",21198,35.84,-101.35,"WEST","A"),
    ("48235","Irion",1536,31.30,-100.98,"WEST","F"),
    ("48237","Jack",8935,33.25,-98.18,"NORTH","B"),
    ("48239","Jackson",14837,28.96,-96.57,"COAST","N"),
    ("48241","Jasper",35505,30.79,-94.01,"EAST","I"),
    ("48243","Jeff Davis",2274,30.60,-104.11,"FWEST","F"),
    ("48245","Jefferson",252358,29.97,-94.16,"EAST","I"),
    ("48247","Jim Hogg",5200,27.04,-98.69,"SOUTH","N"),
    ("48249","Jim Wells",40685,27.73,-98.10,"SOUTH","N"),
    ("48251","Johnson",183527,32.38,-97.37,"NCENT","G"),
    ("48253","Jones",19958,32.73,-99.88,"NCENT","F"),
    ("48255","Karnes",15387,28.89,-97.86,"SOUTH","N"),
    ("48257","Kaufman",138494,32.60,-96.28,"NCENT","C"),
    ("48259","Kendall",46987,29.94,-98.71,"SCENT","L"),
    ("48261","Kenedy",404,26.93,-97.87,"SOUTH","N"),
    ("48263","Kent",762,33.18,-100.79,"WEST","O"),
    ("48265","Kerr",52600,30.04,-99.35,"SCENT","J"),
    ("48267","Kimble",4607,30.49,-99.75,"SCENT","J"),
    ("48269","King",272,33.62,-100.26,"WEST","B"),
    ("48271","Kinney",3675,29.35,-100.42,"SOUTH","L"),
    ("48273","Kleberg",31425,27.43,-97.88,"SOUTH","N"),
    ("48275","Knox",3664,33.61,-99.75,"NORTH","B"),
    ("48277","Lamar",49859,33.67,-95.57,"NORTH","D"),
    ("48279","Lamb",13262,34.07,-102.35,"WEST","O"),
    ("48281","Lampasas",21891,31.20,-98.18,"SCENT","G"),
    ("48283","La Salle",7418,28.34,-99.10,"SOUTH","L"),
    ("48285","Lavaca",20154,29.38,-96.93,"COAST","N"),
    ("48287","Lee",17239,30.32,-96.97,"EAST","K"),
    ("48289","Leon",17873,31.30,-95.98,"EAST","K"),
    ("48291","Liberty",88219,30.15,-94.82,"COAST","I"),
    ("48293","Limestone",23437,31.55,-96.59,"EAST","G"),
    ("48295","Lipscomb",3233,36.28,-100.27,"WEST","A"),
    ("48297","Live Oak",12388,28.35,-98.12,"SOUTH","N"),
    ("48299","Llano",21795,30.75,-98.68,"SCENT","J"),
    ("48301","Loving",64,31.85,-103.53,"FWEST","F"),
    ("48303","Lubbock",321372,33.57,-101.89,"WEST","O"),
    ("48305","Lynn",5765,33.18,-101.82,"WEST","O"),
    ("48307","McCulloch",7984,31.20,-99.35,"NCENT","F"),
    ("48309","McLennan",256623,31.55,-97.15,"EAST","G"),
    ("48311","McMullen",707,28.35,-99.35,"SOUTH","L"),
    ("48313","Madison",14128,30.96,-95.92,"EAST","K"),
    ("48315","Marion",10083,32.80,-94.36,"EAST","D"),
    ("48317","Martin",5771,32.30,-101.95,"WEST","F"),
    ("48319","Mason",4274,30.75,-99.23,"SCENT","J"),
    ("48321","Matagorda",36643,28.80,-96.01,"COAST","H"),
    ("48323","Maverick",58722,28.74,-100.31,"SOUTH","L"),
    ("48325","Medina",51584,29.35,-99.11,"SCENT","L"),
    ("48327","Menard",2138,30.92,-99.78,"NCENT","F"),
    ("48329","Midland",169831,32.00,-102.11,"WEST","F"),
    ("48331","Milam",24664,30.79,-96.97,"EAST","K"),
    ("48333","Mills",4873,31.49,-98.59,"NCENT","G"),
    ("48335","Mitchell",9134,32.30,-100.92,"WEST","F"),
    ("48337","Montague",19818,33.67,-97.72,"NORTH","B"),
    ("48339","Montgomery",620443,30.30,-95.50,"COAST","H"),
    ("48341","Moore",20940,35.84,-101.89,"WEST","A"),
    ("48343","Morris",12388,33.10,-94.73,"EAST","D"),
    ("48345","Motley",1200,34.08,-100.79,"WEST","B"),
    ("48347","Nacogdoches",65558,31.61,-94.65,"EAST","D"),
    ("48349","Navarro",50114,32.04,-96.48,"EAST","G"),
    ("48351","Newton",13595,30.78,-93.74,"EAST","I"),
    ("48353","Nolan",14688,32.30,-100.41,"WEST","F"),
    ("48355","Nueces",343223,27.72,-97.40,"SOUTH","N"),
    ("48357","Ochiltree",9836,36.28,-100.82,"WEST","A"),
    ("48359","Oldham",2072,35.40,-102.60,"WEST","A"),
    ("48361","Orange",83396,30.10,-93.89,"EAST","I"),
    ("48363","Palo Pinto",29189,32.75,-98.31,"NORTH","G"),
    ("48365","Panola",23440,31.98,-94.31,"EAST","D"),
    ("48367","Parker",147195,32.78,-97.80,"NCENT","C"),
    ("48369","Parmer",9605,34.53,-102.78,"WEST","O"),
    ("48371","Pecos",15823,30.79,-102.72,"FWEST","F"),
    ("48373","Polk",50198,30.79,-94.83,"EAST","I"),
    ("48375","Potter",117415,35.40,-101.89,"WEST","B"),
    ("48377","Presidio",6131,29.85,-104.35,"FWEST","F"),
    ("48379","Rains",12514,32.87,-95.79,"EAST","D"),
    ("48381","Randall",138164,34.97,-101.89,"WEST","B"),
    ("48383","Reagan",3765,31.37,-101.53,"WEST","F"),
    ("48385","Real",3389,29.83,-99.82,"SOUTH","J"),
    ("48387","Red River",12023,33.63,-95.05,"NORTH","D"),
    ("48389","Reeves",15976,31.32,-103.70,"FWEST","F"),
    ("48391","Refugio",7236,28.32,-97.16,"SOUTH","N"),
    ("48393","Roberts",854,35.84,-100.82,"WEST","A"),
    ("48395","Robertson",16952,31.03,-96.51,"EAST","K"),
    ("48397","Rockwall",107624,32.92,-96.42,"NCENT","C"),
    ("48399","Runnels",10264,31.83,-99.97,"NCENT","F"),
    ("48401","Rusk",54406,32.11,-94.78,"EAST","D"),
    ("48403","Sabine",10542,31.34,-93.85,"EAST","I"),
    ("48405","San Augustine",8327,31.39,-94.17,"EAST","I"),
    ("48407","San Jacinto",29850,30.58,-95.17,"EAST","I"),
    ("48409","San Patricio",67046,27.99,-97.52,"SOUTH","N"),
    ("48411","San Saba",6131,31.22,-98.72,"NCENT","J"),
    ("48413","Schleicher",3461,30.89,-100.53,"WEST","F"),
    ("48415","Scurry",17239,32.74,-100.92,"WEST","F"),
    ("48417","Shackelford",3311,32.74,-99.35,"NCENT","F"),
    ("48419","Shelby",25274,31.79,-94.15,"EAST","D"),
    ("48421","Sherman",3034,36.28,-101.89,"WEST","A"),
    ("48423","Smith",233479,32.37,-95.27,"EAST","D"),
    ("48425","Somervell",9128,32.22,-97.78,"NORTH","G"),
    ("48427","Starr",65920,26.56,-98.73,"SOUTH","M"),
    ("48429","Stephens",9366,32.74,-98.84,"NCENT","F"),
    ("48431","Sterling",1291,31.83,-101.04,"WEST","F"),
    ("48433","Stonewall",1350,33.18,-100.26,"WEST","B"),
    ("48435","Sutton",3776,30.49,-100.53,"WEST","F"),
    ("48437","Swisher",7334,34.53,-101.73,"WEST","O"),
    ("48439","Tarrant",2110640,32.77,-97.29,"NCENT","C"),
    ("48441","Taylor",141284,32.30,-99.89,"NCENT","F"),
    ("48443","Terrell",776,30.22,-102.07,"FWEST","F"),
    ("48445","Terry",12337,33.17,-102.34,"WEST","O"),
    ("48447","Throckmorton",1501,33.18,-99.21,"NORTH","B"),
    ("48449","Titus",32750,33.22,-94.97,"EAST","D"),
    ("48451","Tom Green",119679,31.41,-100.44,"WEST","F"),
    ("48453","Travis",1290188,30.33,-97.77,"SCENT","K"),
    ("48455","Trinity",14651,31.09,-95.14,"EAST","I"),
    ("48457","Tyler",21672,30.78,-94.38,"EAST","I"),
    ("48459","Upshur",41753,32.74,-94.94,"EAST","D"),
    ("48461","Upton",3657,31.37,-102.03,"WEST","F"),
    ("48463","Uvalde",27763,29.35,-99.78,"SOUTH","L"),
    ("48465","Val Verde",49025,29.89,-101.15,"SOUTH","J"),
    ("48467","Van Zandt",56590,32.56,-95.84,"EAST","D"),
    ("48469","Victoria",92084,28.80,-96.98,"COAST","N"),
    ("48471","Walker",72971,30.79,-95.57,"EAST","K"),
    ("48473","Waller",55246,30.00,-95.99,"COAST","H"),
    ("48475","Ward",11998,31.51,-103.10,"FWEST","F"),
    ("48477","Washington",35882,30.21,-96.40,"EAST","K"),
    ("48479","Webb",276652,27.76,-99.47,"SOUTH","L"),
    ("48481","Wharton",41556,29.31,-96.10,"COAST","H"),
    ("48483","Wheeler",5056,35.40,-100.27,"WEST","B"),
    ("48485","Wichita",132230,33.90,-98.72,"NORTH","B"),
    ("48487","Wilbarger",12769,34.08,-99.22,"NORTH","B"),
    ("48489","Willacy",21284,26.48,-97.64,"SOUTH","M"),
    ("48491","Williamson",609709,30.65,-97.60,"SCENT","K"),
    ("48493","Wilson",51584,29.17,-98.08,"SCENT","L"),
    ("48495","Winkler",8010,31.85,-103.05,"FWEST","F"),
    ("48497","Wise",69984,33.22,-97.66,"NORTH","C"),
    ("48499","Wood",46007,32.78,-95.38,"EAST","D"),
    ("48501","Yoakum",8713,33.17,-102.83,"WEST","O"),
    ("48503","Young",18550,33.18,-98.69,"NORTH","B"),
    ("48505","Zapata",14369,26.91,-99.17,"SOUTH","M"),
    ("48507","Zavala",12131,28.87,-99.76,"SOUTH","L"),
]

# ─────────────────────────────────────────────────────────────────────────────
# 2. Growth parameters
#    TDC 2022 county projections → average annual growth rate by region
#    Source: Texas Demographic Center, 2022 Population Projections
# ─────────────────────────────────────────────────────────────────────────────

# Approximate 30-year compound growth rates (2020→2050) by ERCOT zone
# Derived from TDC 2022 projections (scenario 1: 1.0 migration)
ZONE_POP_GROWTH_30YR = {
    "NCENT": 0.55,   # DFW metro — very high
    "SCENT": 0.60,   # Austin-San Antonio corridor — highest in state
    "COAST": 0.45,   # Houston metro — high
    "SOUTH": 0.38,   # Rio Grande Valley + SA fringes
    "NORTH": 0.18,
    "EAST":  0.14,
    "WEST":  0.22,
    "FWEST": 0.08,
}

# High-growth override for specific fast-growing counties (TDC data)
COUNTY_POP_GROWTH_OVERRIDE = {
    "48085": 0.80,  # Collin — fastest growing
    "48121": 0.75,  # Denton
    "48453": 0.72,  # Travis / Austin
    "48491": 0.78,  # Williamson
    "48209": 0.70,  # Hays
    "48257": 0.65,  # Kaufman
    "48139": 0.60,  # Ellis
    "48367": 0.58,  # Parker
    "48397": 0.62,  # Rockwall
    "48091": 0.65,  # Comal
    "48187": 0.60,  # Guadalupe
    "48339": 0.50,  # Montgomery
    "48157": 0.48,  # Fort Bend
    "48029": 0.42,  # Bexar / San Antonio
    "48201": 0.38,  # Harris / Houston
    "48113": 0.30,  # Dallas
    "48439": 0.30,  # Tarrant
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. Water demand parameters (TWDB 2022 State Water Plan)
#    Per-capita water demand (ac-ft/person/decade) by TWDB region
#    Primary driver: municipal demand; includes proportion for agricultural/industrial
# ─────────────────────────────────────────────────────────────────────────────

# Total 2020 water demand per capita (acre-feet per year)
# Based on TWDB SWP 2022 Table 2.1 regional totals / populations
REGION_WATER_PER_CAPITA_2020 = {
    "A": 1.40,  # Panhandle — high agricultural
    "B": 1.10,
    "C": 0.45,  # DFW — mostly municipal
    "D": 0.62,
    "E": 0.95,  # El Paso — mid
    "F": 1.80,  # Permian Basin — high industrial/oil
    "G": 0.68,
    "H": 0.55,  # Houston — mostly municipal
    "I": 0.72,
    "J": 1.20,  # Hill Country
    "K": 0.48,  # Central corridor
    "L": 0.70,
    "M": 0.85,  # Rio Grande Valley — agricultural
    "N": 0.90,
    "O": 1.50,  # South Plains — high agricultural
    "P": 0.50,
}

# TWDB projects per-capita water demand DECLINES over time due to efficiency
# (2022 SWP Table 3.1 — projected municipal demand declines ~0.3% per yr)
WATER_EFFICIENCY_PER_DECADE = -0.03  # 3% reduction per decade in per-capita use

# ─────────────────────────────────────────────────────────────────────────────
# 4. Electricity demand parameters (ERCOT 2024 LTDEF)
#    Peak demand MW per 1000 residents by zone
# ─────────────────────────────────────────────────────────────────────────────

# Approximate 2020 peak demand (MW per 1000 residents) by zone
ZONE_MW_PER_1K_POP_2020 = {
    "NCENT": 2.10,
    "SCENT": 2.00,
    "COAST": 2.40,  # Industrial + petrochemical
    "SOUTH": 1.80,
    "NORTH": 2.20,
    "EAST":  2.30,  # Industrial
    "WEST":  2.80,  # Oil & gas
    "FWEST": 1.90,
}

# ERCOT 2024 LTDEF projected annual demand growth rates by zone (% / yr)
ZONE_ELEC_GROWTH_RATE = {
    "NCENT": 0.035,  # 3.5%/yr — new load, data centers
    "SCENT": 0.040,  # 4.0%/yr — Austin growth
    "COAST": 0.025,
    "SOUTH": 0.030,
    "NORTH": 0.020,
    "EAST":  0.018,
    "WEST":  0.050,  # 5%/yr — Permian Basin new load
    "FWEST": 0.015,
}


def project_pop(pop2020, growth_30yr, decade):
    """Project population at decade (0,10,20,30)."""
    rate_per_decade = (1 + growth_30yr) ** (1/3) - 1
    return round(pop2020 * (1 + rate_per_decade) ** (decade / 10))


def project_water(pop, per_capita, decade):
    """Project water demand (thousand acre-feet) at decade."""
    pc = per_capita * (1 + WATER_EFFICIENCY_PER_DECADE) ** (decade / 10)
    return round(pop * pc / 1000, 2)  # in kAF


def project_elec(pop, mw_per_1k, annual_rate, decade):
    """Project peak electricity demand (MW) at decade."""
    return round(pop / 1000 * mw_per_1k * (1 + annual_rate) ** decade, 1)


# ─────────────────────────────────────────────────────────────────────────────
# 5. New load from projects.csv (existing data)
# ─────────────────────────────────────────────────────────────────────────────

def load_new_load_by_county():
    script_dir = os.path.dirname(__file__)
    proj_path = os.path.join(script_dir, "..", "..", "gen_dashboard", "data", "projects.csv")
    proj_path = os.path.normpath(proj_path)

    new_load = {}  # county_name -> total MW
    if not os.path.exists(proj_path):
        print(f"Warning: projects.csv not found at {proj_path}", file=sys.stderr)
        return new_load

    with open(proj_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            county = row.get("county", "").strip().lower()
            try:
                mw = float(row.get("requested_mw", 0) or 0)
            except ValueError:
                mw = 0
            if county:
                new_load[county] = new_load.get(county, 0) + mw
    return new_load


# ─────────────────────────────────────────────────────────────────────────────
# 6. Also extract new load from the existing qgis2web GeoJSON for all counties
# ─────────────────────────────────────────────────────────────────────────────

def load_gen_growth_by_position():
    """
    Extracts the 'new demand by country large loads_Total_MW' field from
    the existing GeoJSON. Returns a list of (mw, centroid_lat, centroid_lon).
    We can't easily join without county names, so we'll match by order.
    (The GeoJSON features are in the same order as COUNTIES above.)
    """
    script_dir = os.path.dirname(__file__)
    zip_path = os.path.join(script_dir, "..", "..", "map_dashboard",
                            "data-20260414T004454Z-3-001.zip")
    zip_path = os.path.normpath(zip_path)

    import zipfile
    if not os.path.exists(zip_path):
        print(f"Warning: map data zip not found at {zip_path}", file=sys.stderr)
        return []

    with zipfile.ZipFile(zip_path) as zf:
        with zf.open("data/Estimatedgenerationgrowthpercounty_5.js") as f:
            raw = f.read().decode("utf-8")

    raw = re.sub(r'^var \w+ = ', '', raw.strip())
    data = json.loads(raw)
    result = []
    for feat in data["features"]:
        mw = feat["properties"].get("new demand by country large loads_Total_MW")
        result.append(mw)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 7. Main: generate CSVs
# ─────────────────────────────────────────────────────────────────────────────

def main():
    script_dir = os.path.dirname(__file__)
    new_load_by_county = load_new_load_by_county()
    gen_growth_values = load_gen_growth_by_position()

    rows = []
    pop_rows = []
    water_rows = []
    elec_rows = []

    for i, (fips, name, pop2020, lat, lon, zone, twdb) in enumerate(COUNTIES):
        # Population projections
        growth_30yr = COUNTY_POP_GROWTH_OVERRIDE.get(fips, ZONE_POP_GROWTH_30YR.get(zone, 0.15))
        pop_2030 = project_pop(pop2020, growth_30yr, 10)
        pop_2040 = project_pop(pop2020, growth_30yr, 20)
        pop_2050 = project_pop(pop2020, growth_30yr, 30)
        pop_growth_pct = round((pop_2050 - pop2020) / pop2020 * 100, 1)

        # Water demand projections (thousand acre-feet)
        pc = REGION_WATER_PER_CAPITA_2020.get(twdb, 0.70)
        water_2020 = project_water(pop2020, pc, 0)
        water_2030 = project_water(pop_2030, pc, 10)
        water_2040 = project_water(pop_2040, pc, 20)
        water_2050 = project_water(pop_2050, pc, 30)
        water_growth_pct = round((water_2050 - water_2020) / max(water_2020, 0.01) * 100, 1)

        # Electricity demand projections (peak MW)
        mw1k = ZONE_MW_PER_1K_POP_2020.get(zone, 2.0)
        elec_rate = ZONE_ELEC_GROWTH_RATE.get(zone, 0.025)
        elec_2020 = project_elec(pop2020, mw1k, elec_rate, 0)
        elec_2030 = project_elec(pop2020, mw1k, elec_rate, 10)
        elec_2040 = project_elec(pop2020, mw1k, elec_rate, 20)
        elec_2050 = project_elec(pop2020, mw1k, elec_rate, 30)
        elec_growth_pct = round((elec_2050 - elec_2020) / max(elec_2020, 0.01) * 100, 1)

        # New load from projects.csv (MW)
        nl_csv = new_load_by_county.get(name.lower(), 0)
        # Also use qgis2web value if available (index-matched)
        nl_qgis = gen_growth_values[i] if i < len(gen_growth_values) else None
        new_load_mw = nl_qgis if nl_qgis is not None else nl_csv

        rows.append({
            "fips": fips,
            "county": name,
            "lat": lat,
            "lon": lon,
            "ercot_zone": zone,
            "twdb_region": twdb,
            "pop_2020": pop2020,
            "pop_2030": pop_2030,
            "pop_2040": pop_2040,
            "pop_2050": pop_2050,
            "pop_growth_pct": pop_growth_pct,
            "water_2020_kaf": water_2020,
            "water_2030_kaf": water_2030,
            "water_2040_kaf": water_2040,
            "water_2050_kaf": water_2050,
            "water_growth_pct": water_growth_pct,
            "elec_peak_2020_mw": elec_2020,
            "elec_peak_2030_mw": elec_2030,
            "elec_peak_2040_mw": elec_2040,
            "elec_peak_2050_mw": elec_2050,
            "elec_growth_pct": elec_growth_pct,
            "new_load_mw": round(new_load_mw, 2) if new_load_mw is not None else 0.0,
        })

        pop_rows.append({
            "fips": fips, "county": name, "ercot_zone": zone,
            "pop_2020": pop2020, "pop_2030": pop_2030,
            "pop_2040": pop_2040, "pop_2050": pop_2050,
            "growth_pct_2020_2050": pop_growth_pct,
        })

        water_rows.append({
            "fips": fips, "county": name, "twdb_region": twdb,
            "demand_2020_kaf": water_2020, "demand_2030_kaf": water_2030,
            "demand_2040_kaf": water_2040, "demand_2050_kaf": water_2050,
            "growth_pct_2020_2050": water_growth_pct,
        })

        elec_rows.append({
            "fips": fips, "county": name, "ercot_zone": zone,
            "peak_mw_2020": elec_2020, "peak_mw_2030": elec_2030,
            "peak_mw_2040": elec_2040, "peak_mw_2050": elec_2050,
            "growth_pct_2020_2050": elec_growth_pct,
        })

    def write_csv(filename, fieldnames, data_rows):
        path = os.path.join(script_dir, filename)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_rows)
        print(f"Wrote {len(data_rows)} rows → {path}")

    write_csv("merged_county_data.csv", list(rows[0].keys()), rows)
    write_csv("population_projections.csv", list(pop_rows[0].keys()), pop_rows)
    write_csv("water_demand.csv", list(water_rows[0].keys()), water_rows)
    write_csv("electricity_demand.csv", list(elec_rows[0].keys()), elec_rows)


if __name__ == "__main__":
    main()
