#!/usr/bin/env python
# encoding: utf-8

name = "Prenol"
shortDesc = ""
longDesc = """
ARC v1.1.0
ARC project Prenol

Levels of theory used:

Conformers:       wb97xd/def2svp
TS guesses:       wb97xd/def2svp
Composite method: cbs-qb3 (using a fine grid)
Frequencies:      b3lyp/cbsb7
Rotor scans:      b3lyp/cbsb7
Using bond additivity corrections for thermo

Using the following ESS settings: {'gaussian': ['c3ddb']}

Considered the following species and TSs:
Species CC(C)=CCO (run time: 21:12:12)
Species CC(C)([CH]CO)OO (run time: 6 days, 18:18:56)
Species C[C](C)C(CO)OO (run time: 7 days, 2:36:50)

Overall time since project initiation: 00:00:01
"""
entry(
    index=0,
    label="CC(C)=CCO",
    molecule="""
1  O u0 p2 c0 {2,S} {16,S}
2  C u0 p0 c0 {1,S} {6,S} {7,S} {8,S}
3  C u0 p0 c0 {5,S} {9,S} {10,S} {11,S}
4  C u0 p0 c0 {5,S} {12,S} {13,S} {14,S}
5  C u0 p0 c0 {3,S} {4,S} {6,D}
6  C u0 p0 c0 {2,S} {5,D} {15,S}
7  H u0 p0 c0 {2,S}
8  H u0 p0 c0 {2,S}
9  H u0 p0 c0 {3,S}
10 H u0 p0 c0 {3,S}
11 H u0 p0 c0 {3,S}
12 H u0 p0 c0 {4,S}
13 H u0 p0 c0 {4,S}
14 H u0 p0 c0 {4,S}
15 H u0 p0 c0 {6,S}
16 H u0 p0 c0 {1,S}
""",
    thermo=NASA(
        polynomials=[
            NASAPolynomial(coeffs=[3.80293, 0.0216197, 0.000487654, -2.86875e-06,
                                   5.06836e-09, -25676.3, 10.8993], Tmin=(10, 'K'), Tmax=(200.013, 'K')),
            NASAPolynomial(coeffs=[5.15024, 0.0419693, -1.96387e-05, 4.30488e-09, -
                                   3.55243e-13, -25824.7, 4.20281], Tmin=(200.013, 'K'), Tmax=(3000, 'K')),
        ],
        Tmin=(10, 'K'),
        Tmax=(3000, 'K'),
        E0=(-213.231, 'kJ/mol'),
        Cp0=(33.2579, 'J/(mol*K)'),
        CpInf=(365.837, 'J/(mol*K)'),
    ),
    shortDesc="""""",
    longDesc="""
Bond corrections: {'H-O': 1, 'C-O': 1, 'C-C': 3, 'C-H': 9, 'C=C': 1}
1D rotors:
pivots: [1, 2], dihedral: [7, 1, 2, 3], rotor symmetry: 3, max scan energy: 8.74 kJ/mol
pivots: [2, 3], dihedral: [1, 2, 3, 10], rotor symmetry: 3, max scan energy: 5.19 kJ/mol
pivots: [4, 5], dihedral: [2, 4, 5, 6], rotor symmetry: 1, max scan energy: 21.92 kJ/mol
Troubleshot with the following constraints and 8.0 degrees resolution:
D 1 2 3 12 F
D 4 5 6 16 F
pivots: [5, 6], dihedral: [4, 5, 6, 16], rotor symmetry: 1, max scan energy: 12.47 kJ/mol
Troubleshot with the following constraints and 8.0 degrees resolution:
D 13 4 5 15 F


External symmetry: 1, optical isomers: 2

Geometry:
C      -1.39568100    1.52848300   -0.00216000
C      -0.40266800    0.41160100   -0.21081300
C      -0.99762900   -0.97208100   -0.12764100
C       0.89060700    0.67897900   -0.43343500
C       2.01563100   -0.28316000   -0.67672100
O       2.74198600    0.04398900   -1.86741500
H      -0.92369900    2.50993300   -0.07294900
H      -2.20064900    1.47918300   -0.74492200
H      -1.87384300    1.44886000    0.98123800
H      -1.83979900   -1.06870600   -0.82223300
H      -0.28342400   -1.76517300   -0.34616700
H      -1.40049200   -1.15435400    0.87545900
H       1.20133600    1.72190000   -0.46663700
H       2.75424100   -0.21239800    0.12757500
H       1.66790600   -1.32225000   -0.70730000
H       2.10186800    0.07939500   -2.58570000
""",
)

entry(
    index=1,
    label="CC(C)([CH]CO)OO",
    molecule="""
multiplicity 2
1  C u0 p0 c0 {2,S} {3,S} {5,S} {6,S}
2  C u0 p0 c0 {1,S} {9,S} {10,S} {11,S}
3  C u0 p0 c0 {1,S} {12,S} {13,S} {14,S}
4  C u0 p0 c0 {5,S} {7,S} {15,S} {16,S}
5  C u1 p0 c0 {1,S} {4,S} {17,S}
6  O u0 p2 c0 {1,S} {8,S}
7  O u0 p2 c0 {4,S} {18,S}
8  O u0 p2 c0 {6,S} {19,S}
9  H u0 p0 c0 {2,S}
10 H u0 p0 c0 {2,S}
11 H u0 p0 c0 {2,S}
12 H u0 p0 c0 {3,S}
13 H u0 p0 c0 {3,S}
14 H u0 p0 c0 {3,S}
15 H u0 p0 c0 {4,S}
16 H u0 p0 c0 {4,S}
17 H u0 p0 c0 {5,S}
18 H u0 p0 c0 {7,S}
19 H u0 p0 c0 {8,S}
""",
    thermo=NASA(
        polynomials=[
            NASAPolynomial(coeffs=[3.74643, 0.0261425, 0.000468369, -2.30736e-06,
                                   3.91115e-09, -31171.6, 12.3529], Tmin=(10, 'K'), Tmax=(148.294, 'K')),
            NASAPolynomial(coeffs=[1.85418, 0.0771824, -4.78962e-05, 1.35214e-08, -
                                   1.44317e-12, -31115.5, 17.8705], Tmin=(148.294, 'K'), Tmax=(3000, 'K')),
        ],
        Tmin=(10, 'K'),
        Tmax=(3000, 'K'),
        E0=(-258.646, 'kJ/mol'),
        Cp0=(33.2579, 'J/(mol*K)'),
        CpInf=(428.195, 'J/(mol*K)'),
    ),
    shortDesc="""""",
    longDesc="""
Bond corrections: {'H-O': 2, 'C-O': 2, 'C-C': 4, 'C-H': 9, 'O-O': 1}
1D rotors:
pivots: [1, 2], dihedral: [10, 1, 2, 3], rotor symmetry: 3, max scan energy: 12.65 kJ/mol
pivots: [2, 3], dihedral: [1, 2, 3, 13], rotor symmetry: 3, max scan energy: 11.76 kJ/mol
pivots: [2, 4], dihedral: [1, 2, 4, 6], rotor symmetry: 1, max scan energy: 39.24 kJ/mol
Troubleshot with the following constraints and 8.0 degrees resolution:
D 5 4 6 16 F
D 16 6 7 18 F
D 2 8 9 19 F
pivots: [2, 8], dihedral: [1, 2, 8, 9], rotor symmetry: 1, max scan energy: 72.87 kJ/mol
Troubleshot with the following constraints and 8.0 degrees resolution:
D 5 4 6 16 F
D 3 2 4 6 F
D 16 6 7 18 F
D 2 8 9 19 F
pivots: [4, 6], dihedral: [2, 4, 6, 7], rotor symmetry: 1, max scan energy: 52.31 kJ/mol
Troubleshot with the following constraints and 8.0 degrees resolution:
D 3 2 4 6 F
D 16 6 7 18 F
D 2 8 9 19 F
pivots: [6, 7], dihedral: [4, 6, 7, 18], rotor symmetry: 1, max scan energy: 55.40 kJ/mol
Troubleshot with the following constraints and 8.0 degrees resolution:
D 4 2 8 9 F
D 2 4 5 6 F
D 1 2 4 5 F
D 2 4 6 7 F
D 2 8 9 19 F
pivots: [8, 9], dihedral: [2, 8, 9, 19], rotor symmetry: 1, max scan energy: 55.23 kJ/mol
Troubleshot with the following constraints and 8.0 degrees resolution:
D 3 2 4 6 F
D 5 4 6 16 F
D 16 6 7 18 F


External symmetry: 1, optical isomers: 2

Geometry:
C      -1.89066400   -0.70925500   -0.27199600
C      -0.60118200    0.07805600   -0.01881100
C       0.58645700   -0.54509600   -0.77792400
C      -0.29220300    0.18897400    1.45190100
H      -0.68316400   -0.56844000    2.12482700
C       0.47703200    1.33266400    2.01252900
O      -0.36723900    2.49365600    2.28833500
O      -0.67996600    1.39301300   -0.61896800
O      -1.81160600    2.11950600   -0.07478900
H      -1.81965900   -1.71135300    0.15984400
H      -2.06390700   -0.80166500   -1.34610400
H      -2.73955700   -0.19007600    0.17183500
H       0.37445200   -0.54838500   -1.84970600
H       1.50120900    0.02613500   -0.60813900
H       0.74723900   -1.57231800   -0.44437900
H       1.20904700    1.70777800    1.29655700
H       0.99883600    1.04789600    2.93178900
H      -0.99407600    2.23551400    2.97410900
H      -1.39277400    2.53726100    0.70415100
""",
)

entry(
    index=2,
    label="C[C](C)C(CO)OO",
    molecule="""
multiplicity 2
1  C u0 p0 c0 {2,S} {5,S} {6,S} {9,S}
2  C u0 p0 c0 {1,S} {7,S} {10,S} {11,S}
3  C u0 p0 c0 {5,S} {12,S} {13,S} {14,S}
4  C u0 p0 c0 {5,S} {15,S} {16,S} {17,S}
5  C u1 p0 c0 {1,S} {3,S} {4,S}
6  O u0 p2 c0 {1,S} {8,S}
7  O u0 p2 c0 {2,S} {18,S}
8  O u0 p2 c0 {6,S} {19,S}
9  H u0 p0 c0 {1,S}
10 H u0 p0 c0 {2,S}
11 H u0 p0 c0 {2,S}
12 H u0 p0 c0 {3,S}
13 H u0 p0 c0 {3,S}
14 H u0 p0 c0 {3,S}
15 H u0 p0 c0 {4,S}
16 H u0 p0 c0 {4,S}
17 H u0 p0 c0 {4,S}
18 H u0 p0 c0 {7,S}
19 H u0 p0 c0 {8,S}
""",
    thermo=NASA(
        polynomials=[
            NASAPolynomial(coeffs=[2.97394, 0.10615, -0.000288858, 6.13999e-07, -
                                   5.11104e-10, -30578.3, 13.899], Tmin=(10, 'K'), Tmax=(377.623, 'K')),
            NASAPolynomial(coeffs=[4.21142, 0.0688843, -4.48724e-05, 1.38517e-08, -
                                   1.63002e-12, -30499.5, 11.4146], Tmin=(377.623, 'K'), Tmax=(3000, 'K')),
        ],
        Tmin=(10, 'K'),
        Tmax=(3000, 'K'),
        E0=(-254.259, 'kJ/mol'),
        Cp0=(33.2579, 'J/(mol*K)'),
        CpInf=(428.195, 'J/(mol*K)'),
    ),
    shortDesc="""""",
    longDesc="""
Bond corrections: {'H-O': 2, 'C-O': 2, 'C-C': 4, 'C-H': 9, 'O-O': 1}
1D rotors:
pivots: [1, 2], dihedral: [9, 1, 2, 3], rotor symmetry: 3, max scan energy: 5.28 kJ/mol
Troubleshot with the following constraints and 8.0 degrees resolution:
D 11 9 1 2 F
D 1 2 3 4 F
D 10 9 1 2 F
D 1 2 3 4 F
D 1 2 3 14 F
D 1 2 4 5 F
pivots: [2, 3], dihedral: [1, 2, 3, 12], rotor symmetry: 3, max scan energy: 1.76 kJ/mol
pivots: [2, 4], dihedral: [1, 2, 4, 5], rotor symmetry: 1, max scan energy: 28.99 kJ/mol
Troubleshot with the following constraints and 8.0 degrees resolution:
D 2 4 7 8 F
D 3 1 2 4 F
D 11 1 2 4 F
D 4 2 3 12 F
D 4 7 8 19 F
pivots: [4, 5], dihedral: [2, 4, 5, 6], rotor symmetry: 1, max scan energy: 37.93 kJ/mol
Troubleshot with the following constraints and 8.0 degrees resolution:
D 1 2 4 7 F
D 1 2 3 13 F
D 9 1 2 4 F
D 16 5 6 18 F
D 4 7 8 19 F
pivots: [4, 7], dihedral: [2, 4, 7, 8], rotor symmetry: 1, max scan energy: 48.36 kJ/mol
Troubleshot with the following constraints and 8.0 degrees resolution:
D 4 5 6 18 F
D 5 2 4 7 F
D 1 2 3 14 F
D 11 1 2 3 F
D 3 2 4 15 F
D 4 7 8 19 F
pivots: [5, 6], dihedral: [4, 5, 6, 18], rotor symmetry: 1, max scan energy: 22.54 kJ/mol
pivots: [7, 8], dihedral: [4, 7, 8, 19], rotor symmetry: 1, max scan energy: 21.29 kJ/mol
Troubleshot with the following constraints and 8.0 degrees resolution:
D 1 2 3 14 F
D 11 1 2 4 F
D 3 2 4 5 F


External symmetry: 1, optical isomers: 2

Geometry:
C      -1.26088600   -0.67132700   -1.17863100
C      -0.75916200    0.22016200   -0.08698300
C      -1.74338600    0.87289000    0.82754500
C       0.69581500    0.22475200    0.25988000
C       1.21283900   -1.07723500    0.90118200
O       2.56734600   -0.96657800    1.29379400
O       1.54517800    0.35321600   -0.90581000
O       1.51865100    1.73008000   -1.35029500
H      -1.72186800   -1.58962400   -0.77990100
H      -0.45756200   -0.97361400   -1.85372300
H      -2.04099500   -0.17723600   -1.77073400
H      -2.21626100    0.14930400    1.51206700
H      -1.27716100    1.64426000    1.44605500
H      -2.56419400    1.33583900    0.26636400
H       0.93396500    1.05235600    0.93522800
H       1.06063000   -1.91084300    0.20112900
H       0.63227100   -1.28151900    1.80321700
H       3.04613700   -0.64046400    0.52278900
H       0.83264700    1.69412000   -2.03216400
""",
)
