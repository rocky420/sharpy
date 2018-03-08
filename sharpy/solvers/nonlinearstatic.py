import numpy as np

import sharpy.structure.utils.xbeamlib as xbeamlib
import sharpy.utils.cout_utils as cout
import sharpy.utils.settings as settings
from sharpy.utils.solver_interface import solver, BaseSolver


@solver
class NonLinearStatic(BaseSolver):
    solver_id = 'NonLinearStatic'

    def __init__(self):
        # settings list
        self.settings_types = dict()
        self.settings_default = dict()

        self.settings_types['print_info'] = 'bool'
        self.settings_default['print_info'] = True

        self.settings_types['max_iterations'] = 'int'
        self.settings_default['max_iterations'] = 100

        self.settings_types['num_load_steps'] = 'int'
        self.settings_default['num_load_steps'] = 5

        self.settings_types['delta_curved'] = 'float'
        self.settings_default['delta_curved'] = 1e-5

        self.settings_types['gravity_on'] = 'bool'
        self.settings_default['gravity_on'] = False

        self.settings_types['gravity'] = 'float'
        self.settings_default['gravity'] = 9.81

        self.settings_types['min_delta'] = 'float'
        self.settings_default['min_delta'] = 1e-7

        self.data = None
        self.settings = None

    def initialise(self, data, custom_settings=None):
        self.data = data
        if custom_settings is None:
            self.settings = data.settings[self.solver_id]
        else:
            self.settings = custom_settings
        settings.to_custom_types(self.settings, self.settings_types, self.settings_default)

    def run(self):
        # cout.cout_wrap('Running non linear static solver...', 2)
        xbeamlib.cbeam3_solv_nlnstatic(self.data.structure, self.settings, self.data.ts)
        return self.data

    def next_step(self):
        self.data.structure.next_step()

    def extract_resultants(self):
        # gravity_forces, applied_forces = xbeamlib.cbeam3_solv_compute_resultant(self.data.structure.timestep_info[-1],
        #                                                                         self.data.structure,
        #                                                                         self.settings)



        applied_forces = self.data.structure.nodal_b_for_2_a_for(self.data.structure.timestep_info[-1].steady_applied_forces,
                                                                 self.data.structure.timestep_info[-1])

        gravity_forces = self.data.structure.timestep_info[-1].gravity_forces[:]

        forces = gravity_forces[:, 0:3] + applied_forces[:, 0:3]
        moments = gravity_forces[:, 3:6] + applied_forces[:, 3:6]
        # other moment contribution
        for i_node in range(self.data.structure.num_node):
            moments[i_node, :] += np.cross(self.data.structure.timestep_info[-1].pos[i_node, :],
                                           forces[i_node, :])
        return np.sum(forces, axis=0), np.sum(moments, axis=0)


