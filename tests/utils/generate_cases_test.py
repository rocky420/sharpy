import sharpy.utils.generate_cases as gc
import unittest
import numpy as np
import os
# import fnmatch

class TestGenerateCases(unittest.TestCase):
    """
    Tests the generate_cases module
    """

    def test_01(self):

        nodes_per_elem = 3

        # beam1: uniform and symmetric with aerodynamic properties equal to zero
        nnodes1 = 11
        length1  = 10.
        mass_per_unit_length = 1.
        mass_iner = 1e-4
        EA = 1e9
        GA = 1e9
        GJ = 1e9
        EI = 1e9

        # Create beam1
        beam1 = gc.AeroelasticInformation()
        # Structural information
        beam1.StructuralInformation.num_node = nnodes1
        beam1.StructuralInformation.num_node_elem = nodes_per_elem
        beam1.StructuralInformation.compute_basic_num_elem()
        beam1.StructuralInformation.set_to_zero(beam1.StructuralInformation.num_node_elem, beam1.StructuralInformation.num_node, beam1.StructuralInformation.num_elem)
        node_pos = np.zeros((nnodes1, 3), )
        node_pos[:, 2] = np.linspace(0.0, length1, nnodes1)
        beam1.StructuralInformation.generate_uniform_sym_beam(node_pos, mass_per_unit_length, mass_iner, EA, GA, GJ, EI, num_node_elem = 3, y_BFoR = 'y_AFoR', num_lumped_mass=1)
        beam1.StructuralInformation.lumped_mass_nodes[0] = 5
        beam1.StructuralInformation.lumped_mass[0] = 0.5
        beam1.StructuralInformation.lumped_mass_inertia[0] = np.eye(3)
        beam1.StructuralInformation.lumped_mass_position[0,:] = np.zeros((3,),)
        # Aerodynamic information
        beam1.AerodynamicInformation.set_to_zero(beam1.StructuralInformation.num_node_elem, beam1.StructuralInformation.num_node, beam1.StructuralInformation.num_elem)

        # beam2
        beam2 = beam1.copy()
        beam2.StructuralInformation.rotate_around_origin(np.array([0.,1.,0.]), 90*np.pi/180.)
        beam2.StructuralInformation.coordinates[:,2] += length1
        beam2.StructuralInformation.lumped_mass_nodes[0] = 0
        airfoil = np.zeros((1,20,2),)
        airfoil[0,:,0] = np.linspace(0.,1.,20)
        beam2.AerodynamicInformation.create_one_uniform_aerodynamics(
                                            beam2.StructuralInformation,
                                            chord = 1.,
                                            twist = 0.,
                                            sweep = 0.,
                                            num_chord_panels = 4,
                                            m_distribution = 'uniform',
                                            elastic_axis = 0.5,
                                            num_points_camber = 20,
                                            airfoil = airfoil)

        # beam3
        nnodes3 = 9
        beam3 = gc.AeroelasticInformation()
        # Structural information
        beam3.StructuralInformation.num_node = nnodes3
        beam3.StructuralInformation.num_node_elem = nodes_per_elem
        beam3.StructuralInformation.compute_basic_num_elem()
        beam3.StructuralInformation.set_to_zero(beam3.StructuralInformation.num_node_elem, beam3.StructuralInformation.num_node, beam3.StructuralInformation.num_elem)
        node_pos = np.zeros((nnodes3, 3), )
        node_pos[:,0] = length1
        node_pos[:, 2] = np.linspace(length1, 0.0, nnodes3)

        beam3.StructuralInformation.generate_uniform_beam(node_pos, mass_per_unit_length, mass_iner, 2.*mass_iner, 3.*mass_iner, np.zeros((3,),), EA, GA, 2.0*GA, GJ, EI, 4.*EI, num_node_elem = 3, y_BFoR = 'y_AFoR', num_lumped_mass=1)
        beam3.StructuralInformation.lumped_mass_nodes[0] = nnodes3-1
        beam3.StructuralInformation.lumped_mass[0] = 0.25
        beam3.StructuralInformation.lumped_mass_inertia[0] = 2.*np.eye(3)
        beam3.StructuralInformation.lumped_mass_position[0,:] = np.zeros((3,),)

        # Aerodynamic information
        airfoils = np.zeros((1, 20, 2), )
        airfoils[0, :, 0] = np.linspace(0., 1., 20)
        beam3.AerodynamicInformation.create_aerodynamics_from_vec(StructuralInformation = beam3.StructuralInformation,
                                     vec_aero_node = np.ones((nnodes3), dtype = bool),
                                     vec_chord = np.linspace(1.,0.1,nnodes3),
                                     vec_twist = 0.1*np.ones((nnodes3,),),
                                     vec_sweep = 0.2*np.ones((nnodes3,), ),
                                     vec_surface_m = 4*np.ones((1,), dtype = int),
                                     vec_surface_distribution = np.zeros((beam3.StructuralInformation.num_elem,), dtype=int),
                                     vec_m_distribution = np.array(['uniform']),
                                     vec_elastic_axis = 0.5*np.ones((nnodes3,), ),
                                     vec_airfoil_distribution = np.zeros((nnodes3,), dtype=int),
                                     airfoils = airfoils)

        beam1.assembly(beam2, beam3)
        beam1.StructuralInformation.boundary_conditions[0] = 1
        beam1.StructuralInformation.boundary_conditions[-1] = -1
        beam1.remove_duplicated_points(1e-3)

        beam1.StructuralInformation.check_StructuralInformation()
        beam1.AerodynamicInformation.check_AerodynamicInformation(beam1.StructuralInformation)
        #beam1.generate_h5_files('/home/arturo/technical_work/05-test_generate_cases', 'test_01')

        # SOLVER CONFIGURATION
        SimInfo = gc.SimulationInformation()
        SimInfo.set_default_values()

        SimInfo.define_uinf(np.array([0.0,1.0,0.0]), 10.)

        SimInfo.solvers['SHARPy']['flow'] = ['BeamLoader',
                                'AerogridLoader',
                                'StaticCoupled',
                                'DynamicCoupled',
                                'AerogridPlot',
                                'BeamPlot'
                                ]
        SimInfo.solvers['SHARPy']['case'] = 'test_01'
        SimInfo.solvers['SHARPy']['route'] = os.path.dirname(os.path.realpath(__file__)) + '/'
        SimInfo.set_variable_all_dicts('dt', 0.05)

        SimInfo.solvers['BeamLoader']['unsteady'] = 'on'

        SimInfo.solvers['AerogridLoader']['unsteady'] = 'on'
        SimInfo.solvers['AerogridLoader']['mstar'] = 13

        # Default values for NonLinearStatic
        # Default values for StaticUvlm
        # Default values for NonLinearDynamicCoupledStep
        # Default values for StepUvlm

        SimInfo.solvers['StaticCoupled']['structural_solver'] = 'NonLinearStatic'
        SimInfo.solvers['StaticCoupled']['structural_solver_settings'] = SimInfo.solvers['NonLinearStatic']
        SimInfo.solvers['StaticCoupled']['aero_solver'] = 'StaticUvlm'
        SimInfo.solvers['StaticCoupled']['aero_solver_settings'] = SimInfo.solvers['StaticUvlm']

        SimInfo.solvers['DynamicCoupled']['structural_solver'] = 'NonLinearDynamicCoupledStep'
        SimInfo.solvers['DynamicCoupled']['structural_solver_settings'] = SimInfo.solvers['NonLinearDynamicCoupledStep']
        SimInfo.solvers['DynamicCoupled']['aero_solver'] = 'StepUvlm'
        SimInfo.solvers['DynamicCoupled']['aero_solver_settings'] = SimInfo.solvers['StepUvlm']
        SimInfo.solvers['DynamicCoupled']['post_processors'] = ['BeamPlot', 'AerogridPlot']
        SimInfo.solvers['DynamicCoupled']['post_processor_settings'] = {'BeamPlot': SimInfo.solvers['BeamPlot'],
                                                                     'AerogridPlot': SimInfo.solvers['AerogridPlot']}
        SimInfo.define_num_steps(20)

        # Define dynamic simulation
        SimInfo.with_forced_vel = True
        SimInfo.for_vel = np.zeros((20,6), dtype=float)
        SimInfo.for_acc = np.zeros((20,6), dtype=float)
        SimInfo.with_dynamic_forces = True
        SimInfo.dynamic_forces = np.zeros((20,beam1.StructuralInformation.num_node,6), dtype=float)

        gc.clean_test_files(SimInfo.solvers['SHARPy']['route'], SimInfo.solvers['SHARPy']['case'])
        SimInfo.generate_solver_file()
        SimInfo.generate_dyn_file(20)
        beam1.generate_h5_files(SimInfo.solvers['SHARPy']['route'], SimInfo.solvers['SHARPy']['case'])



if __name__=='__main__':
    # unittest.main()

    # # Remove old cases
    # if fnmatch.fnmatch(file, '*.fem.h5'):
    #     os.remove(file)
    # if fnmatch.fnmatch(file, '*.dyn.h5'):
    #     os.remove(file)
    # if fnmatch.fnmatch(file, '*.aero.h5'):
    #     os.remove(file)
    # if fnmatch.fnmatch(file, '*.mb.h5'):
    #     os.remove(file)
    # if fnmatch.fnmatch(file, '*.solver.txt'):
    #     os.remove(file)
    # if fnmatch.fnmatch(file, '*.flightcon.txt'):
    #     os.remove(file)

    T=TestGenerateCases()
    # T.setUp()
    T.test_01()