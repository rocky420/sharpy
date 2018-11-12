"""
Generate cases

This library provides functions and classes to help in the definition of SHARPy cases

Examples:

    tests in: tests/utils/generate_cases

Notes:

    To use this library: import sharpy.utils.generate_cases as generate_cases

"""

import numpy as np
import sharpy.utils.algebra as algebra
import h5py as h5


######################################################################
#########################  AUX FUNCTIONS  ############################
######################################################################
def get_airfoil_camber(x, y, n_points_camber):
    """
    get_airfoil_camber

    Define the camber of an airfoil based on its coordinates

    Args:
    	x (np.array): x coordinates of the airfoil surface
    	y (np.array): y coordinates of the airfoil surface
        n_points_camber (int): number of points to define the camber line

    Returns:
        camber_x (np.array): x coordinates of the camber line
    	camber_y (np.array): y coordinates of the camber line

    Notes:
    	The x and y vectors are expected in XFOIL format: TE - suction side - LE - pressure side - TE

    """
    # Returns the airfoil camber for a given set of coordinates (XFOIL format expected)

    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    n = len(x)
    imin_x = 0

    # Look for the minimum x (it will be assumed as the LE position
    for i in range(n):
        if(x[i] < x[imin_x]):
            imin_x = i

    x_suction = np.zeros((imin_x+1, ))
    y_suction = np.zeros((imin_x+1, ))
    x_pressure = np.zeros((n-imin_x, ))
    y_pressure = np.zeros((n-imin_x, ))

    for i in range(0, imin_x+1):
        x_suction[i] = x[imin_x-i]
        y_suction[i] = y[imin_x-i]

    for i in range(imin_x, n):
        x_pressure[i-imin_x] = x[i]
        y_pressure[i-imin_x] = y[i]

    # Compute the camber coordinates
    camber_y = np.zeros((n_points_camber, ))
    camber_x = np.linspace(0.0, 1.0, n_points_camber)

    # camber_y=0.5*(np.interp(camber_x,x[imin_x::-1],y[imin_x::-1])+np.interp(camber_x,x[imin_x:],y[imin_x:]))
    camber_y = 0.5*(np.interp(camber_x, x_suction, y_suction) +
                    np.interp(camber_x, x_pressure, y_pressure))

    # The function should be called as: camber_x, camber_y = get_airfoil_camber(x,y)
    return camber_x, camber_y

def from_node_list_to_elem_matrix(node_list, connectivities):
    """
    from_node_list_to_elem_matrix

    Convert list of properties associated to nodes to matrix of properties associated
    to elements based on the connectivities

    The 'ith' value of the 'node_list' array stores the property of the 'ith' node.
    The 'jth' 'kth' value of the 'elem_matrix' array stores the property of the 'kth' node
    within the 'jth' element

    Args:
        node_list (np.array): Properties of the nodes
        connectivities (np.array): Connectivities between the nodes to form elements

    Returns:
    	elem_matrix (np.array): Properties of the elements
    """
    num_elem = len(connectivities)
    # TODO: change the "3" for self.num_node_elem
    elem_matrix = np.zeros((num_elem,3), dtype=node_list.dtype)
    for ielem in range(num_elem):
        elem_matrix[ielem, :] = node_list[connectivities[ielem, :]]

    return elem_matrix


######################################################################
###############  STRUCTURAL INFORMATION  #############################
######################################################################
class StructuralInformation():
    """
    StructuralInformation

    Structural information needed to build a case
    """

    def __init__(self):
        """
        __init__

        Initialization
        """

        # Variables to write in the h5 file
        self.num_node_elem = None
        self.num_node = None
        self.num_elem = None
        self.coordinates = None
        self.connectivities = None
        self.elem_stiffness = None
        self.stiffness_db = None
        self.elem_mass = None
        self.mass_db = None
        self.frame_of_reference_delta = None
        self.structural_twist = None
        self.boundary_conditions = None
        self.beam_number = None
        self.app_forces = None
        self.lumped_mass_nodes = None
        self.lumped_mass = None
        self.lumped_mass_inertia = None
        self.lumped_mass_position = None

    def copy(self):
        """
        copy

        Returns a copy of the object

        Returns:
        	copied(StructuralInformation): new object with the same properties
        """
        copied = StructuralInformation()
        # Variables to write in the h5 file
        copied.num_node_elem = self.num_node_elem.astype(dtype=int, copy=True)
        copied.num_node = self.num_node.astype(dtype=int, copy=True)
        copied.num_elem = self.num_elem.astype(dtype=int, copy=True)
        copied.coordinates = self.coordinates.astype(dtype=float, copy=True)
        copied.connectivities = self.connectivities.astype(dtype=int, copy=True)
        copied.elem_stiffness = self.elem_stiffness.astype(dtype=int, copy=True)
        copied.stiffness_db = self.stiffness_db.astype(dtype=float, copy=True)
        copied.elem_mass = self.elem_mass.astype(dtype=int, copy=True)
        copied.mass_db = self.mass_db.astype(dtype=float, copy=True)
        copied.frame_of_reference_delta = self.frame_of_reference_delta.astype(dtype=float, copy=True)
        copied.structural_twist = self.structural_twist.astype(dtype=float, copy=True)
        copied.boundary_conditions = self.boundary_conditions.astype(dtype=int, copy=True)
        copied.beam_number = self.beam_number.astype(dtype=int, copy=True)
        copied.app_forces = self.app_forces.astype(dtype=float, copy=True)
        copied.lumped_mass_nodes = self.lumped_mass_nodes.astype(dtype=int, copy=True)
        copied.lumped_mass = self.lumped_mass.astype(dtype=float, copy=True)
        copied.lumped_mass_inertia = self.lumped_mass_inertia.astype(dtype=float, copy=True)
        copied.lumped_mass_position = self.lumped_mass_position.astype(dtype=float, copy=True)

        return copied

    def set_to_zero(self, num_node_elem, num_node, num_elem,
                    num_mass_db = None, num_stiffness_db = None, num_lumped_mass=0):
        """
        set_to_zero

        Sets to zero all the variables

        Args:
            num_node_elem (int): number of nodes per element
            num_node (int): number of nodes
            num_elem (int): number of elements
            num_mass_db (int): number of different mass matrices in the case
            num_stiffness_db (int): number of different stiffness matrices in the case
            num_lumped_mass (int): number of lumped masses in the case
        """

        if num_mass_db is None:
            num_mass_db = self.num_elem
        if num_stiffness_db is None:
            num_stiffness_db = self.num_elem

        self.num_node_elem = num_node_elem
        self.num_node = num_node
        self.num_elem = num_elem
        self.coordinates = np.zeros((num_node, 3), dtype=float)
        self.connectivities = np.zeros((num_elem, num_node_elem), dtype=int)
        self.elem_stiffness = np.zeros((num_elem,), dtype=int)
        self.stiffness_db = np.zeros((num_stiffness_db, 6, 6), dtype=float)
        self.elem_mass = np.zeros((num_elem,), dtype=int)
        self.mass_db = np.zeros((num_mass_db, 6, 6), dtype=float)
        self.frame_of_reference_delta = np.zeros((num_elem, num_node_elem, 3),
                                                 dtype=float)
        self.structural_twist = np.zeros((num_node,), dtype=float)
        self.boundary_conditions = np.zeros((num_node,), dtype=int)
        self.beam_number = np.zeros((num_elem,), dtype=int)
        self.app_forces = np.zeros((num_node, 6), dtype=int)
        if not num_lumped_mass == 0:
            self.lumped_mass_nodes = np.zeros((num_lumped_mass,), dtype=int)
            self.lumped_mass = np.zeros((num_lumped_mass,), dtype=int)
            self.lumped_mass_inertia = np.zeros((num_lumped_mass, 3, 3),
                                                dtype=int)
            self.lumped_mass_position = np.zeros((num_lumped_mass, 3),
                                                 dtype=int)

    def generate_full_structure(self,
                                num_node_elem,
                                num_node,
                                num_elem,
                                coordinates,
                                connectivities,
                                elem_stiffness,
                                stiffness_db,
                                elem_mass,
                                mass_db,
                                frame_of_reference_delta,
                                structural_twist,
                                boundary_conditions,
                                beam_number,
                                app_forces,
                                lumped_mass_nodes = None,
                                lumped_mass = None,
                                lumped_mass_inertia = None,
                                lumped_mass_position = None):
        """
        generate_full_structure

        Defines the whole case from the appropiated variables

        Args:
        	num_node_elem (int): number of nodes per element
            num_node (int): number of nodes
            num_elem (int): number of elements
            coordinates (np.array): nodes coordinates
            connectivities (np.array): element connectivities
            elem_stiffness (np.array): element stiffness index
            stiffness_db (np.array): Stiffness matrices
            elem_mass (np.array): element mass index
            mass_db (np.array): Mass matrices
            frame_of_reference_delta (np.array): element direction of the y axis in the BFoR wrt the AFoR
            structural_twist (np.array): node twist
            boundary_conditions (np.array): node boundary condition
            beam_number (np.array): node beam number
            app_forces (np.array): steady applied follower forces at the nodes
            lumped_mass_nodes (np.array): nodes with lumped masses
            lumped_mass (np.array): value of the lumped masses
            lumped_mass_inertia (np.array): inertia of the lumped masses
            lumped_mass_position (np.array): position of the lumped masses
        """

        self.num_node_elem = num_node_elem
        self.num_node = num_node
        self.num_elem = num_elem
        self.coordinates = coordinates
        self.connectivities = connectivities
        self.elem_stiffness = elem_stiffness
        self.stiffness_db = stiffness_db
        self.elem_mass = elem_mass
        self.mass_db = mass_db
        self.frame_of_reference_delta = frame_of_reference_delta
        self.structural_twist = structural_twist
        self.boundary_conditions = boundary_conditions
        self.beam_number = beam_number
        self.app_forces = app_forces
        if not lumped_mass_nodes == None:
            self.lumped_mass_nodes = lumped_mass_nodes
            self.lumped_mass = lumped_mass
            self.lumped_mass_inertia = lumped_mass_inertia
            self.lumped_mass_position = lumped_mass_position

    def create_frame_of_reference_delta(self, y_BFoR = 'y_AFoR'):
        """
        create_frame_of_reference_delta

        Define the coordinates of the yB axis in the AFoR

        Args:
        	y_BFoR (string): Direction of the yB axis
        """

        if y_BFoR == 'x_AFoR':
            yB = np.array([1.0, 0.0, 0.0])
        elif y_BFoR == 'y_AFoR':
            yB = np.array([0.0, 1.0, 0.0])
        elif y_BFoR == 'z_AFoR':
            yB = np.array([0.0, 0.0, 1.0])
        else:
            print("WARNING: y_BFoR not recognized, using the default value: y_BFoR = y_AFoR")

        # y vector of the B frame of reference
        self.frame_of_reference_delta = np.zeros((self.num_elem,
                                                  self.num_node_elem, 3),
                                                  dtype=float)
        for ielem in range(self.num_elem):
            for inode in range(self.num_node_elem):
                # TODO: do i need to use the connectivities?
                self.frame_of_reference_delta[ielem,inode,:] = yB

    def create_mass_db_from_vector(self,
                                   vec_mass_per_unit_length,
                                   vec_mass_iner_x,
                                   vec_mass_iner_y,
                                   vec_mass_iner_z,
                                   vec_pos_cg_B):

        """
        create_mass_db_from_vector

        Create the mass matrices from the vectors of properties

        Args:
        	vec_mass_per_unit_length (np.array): masses per unit length
            vec_mass_iner_x (np.array): inertias around the x axis
            vec_mass_iner_y (np.array): inertias around the y axis
            vec_mass_iner_z (np.array): inertias around thez axis
            vec_pos_cg_B (np.array): position of the masses
        """

        self.mass_db = np.zeros((len(vec_mass_per_unit_length), 6, 6), dtype=float)
        mass = np.zeros((6, 6),)
        for i in range(len(vec_mass_per_unit_length)):
            mass[0:3, 0:3] = np.eye(3)*vec_mass_per_unit_length[i]
            mass[0:3, 3:6] = -1.0*vec_mass_per_unit_length[i]*algebra.skew(vec_pos_cg_B[i])
            mass[3:6, 0:3] = -1.0*mass[0:3, 3:6]
            mass[3:6, 3:6] = np.diag([vec_mass_iner_x[i],
                                      vec_mass_iner_y[i],
                                      vec_mass_iner_z[i]])

            self.mass_db[i] = mass

    def create_stiff_db_from_vector(self,
                                    vec_EA,
                                    vec_GAy,
                                    vec_GAz,
                                    vec_GJ,
                                    vec_EIy,
                                    vec_EIz):
        """
        create_stiff_db_from_vector

        Create the stiffness matrices from the vectors of properties

        Args:
            vec_EA (np.array): Axial stiffness
            vec_GAy (np.array): Shear stiffness in the y direction
            vec_GAz (np.array): Shear stiffness in the z direction
            vec_GJ (np.array): Torsional stiffness
            vec_EIy (np.array): Bending stiffness in the y direction
            vec_EIz (np.array): Bending stiffness in the z direction
        """

        self.stiffness_db = np.zeros((len(vec_EA), 6, 6),)
        for i in range(len(vec_EA)):
            self.stiffness_db[i] = np.diag([vec_EA[i],
                                            vec_GAy[i],
                                            vec_GAz[i],
                                            vec_GJ[i],
                                            vec_EIy[i],
                                            vec_EIz[i]])

    def create_simple_connectivities(self):
        """
        create_simple_connectivities

        Create the matrix of connectivities for one single beam with the nodes
        ordered in increasing xB direction
        """
        self.connectivities = np.zeros((self.num_elem, self.num_node_elem),
                                       dtype=int)
        for ielem in range(self.num_elem):
            self.connectivities[ielem, :] = (np.array([0, 2, 1], dtype=int) +
                                             ielem*(self.num_node_elem - 1))

    def rotate_around_origin(self, axis, angle):
        """
        rotate_around_origin

        Rotates a structure

        Args:
        	axis (np.array): axis of rotation
        	angle (float): angle of rotation in radians
        """

        rot = algebra.rotation_matrix_around_axis(axis, angle)
        for inode in range(len(self.coordinates)):
            self.coordinates[inode,:] = np.dot(rot, self.coordinates[inode,:])

        for ielem in range(self.num_elem):
            for inode in range(self.num_node_elem):
                self.frame_of_reference_delta[ielem,inode,:] = np.dot(rot, self.frame_of_reference_delta[ielem,inode, :])

    def compute_basic_num_elem(self):
        """
        compute_basic_num_elem

        It computes the number of elements when no nodes are shared between beams
        """
        if ((self.num_node-1) % (self.num_node_elem-1)) == 0:
            self.num_elem = int((self.num_node-1)/(self.num_node_elem-1))
        else:
            print("ERROR: number of nodes cannot be converted into 3-noded elements")

    def generate_uniform_sym_beam(self, node_pos, mass_per_unit_length, mass_iner, EA, GA, GJ, EI, num_node_elem = 3, y_BFoR = 'y_AFoR', num_lumped_mass=0):
        """
        generate_uniform_sym_beam

        Generates the input data for SHARPy of a uniform symmetric beam

        Args:
            node_pos (np.array): coordinates of the nodes
            mass_per_unit_length (float): mass per unit length
            mass_iner (float): Inertia of the mass
            EA (float): Axial stiffness
            GA (float): Shear stiffness
            GJ (float): Torsional stiffness
            EI (float): Bending stiffness
            num_node_elem (int): number of nodes per element
            y_BFoR (str): orientation of the yB axis
            num_lumped_mass (int): number of lumped masses
        """
        self.generate_uniform_beam(node_pos, mass_per_unit_length, mass_iner, mass_iner, mass_iner, np.zeros((3,),), EA, GA, GA, GJ, EI, EI, num_node_elem, y_BFoR, num_lumped_mass)

    def generate_uniform_beam(self, node_pos, mass_per_unit_length, mass_iner_x, mass_iner_y, mass_iner_z, pos_cg_B, EA, GAy, GAz, GJ, EIy, EIz, num_node_elem = 3, y_BFoR = 'y_AFoR', num_lumped_mass=0):
        """
        generate_uniform_beam

        Generates the input data for SHARPy of a uniform beam

        Args:
            node_pos (np.array): coordinates of the nodes
            mass_per_unit_length (float): mass per unit length
            mass_iner_x (float): Inertia of the mass in the x direction
            mass_iner_y (float): Inertia of the mass in the y direction
            mass_iner_z (float): Inertia of the mass in the z direction
            pos_cg_B (np.array): position of the masses
            EA (np.array): Axial stiffness
            GAy (np.array): Shear stiffness in the y direction
            GAz (np.array): Shear stiffness in the z direction
            GJ (np.array): Torsional stiffness
            EIy (np.array): Bending stiffness in the y direction
            EIz (np.array): Bending stiffness in the z direction
            num_node_elem (int): number of nodes per element
            y_BFoR (str): orientation of the yB axis
            num_lumped_mass (int): number of lumped masses
        """
        self.num_node = len(node_pos)
        self.num_node_elem = num_node_elem
        self.compute_basic_num_elem()

        self.set_to_zero(self.num_node_elem, self.num_node, self.num_elem, 1, 1, num_lumped_mass)
        self.coordinates = node_pos
        self.create_simple_connectivities()
        # self.create_mass_db_from_vector(np.ones((num_elem,),)*mass_per_unit_length,
        #                                np.ones((num_elem,),)*mass_iner_x,
        #                                np.ones((num_elem,),)*mass_iner_y,
        #                                np.ones((num_elem,),)*mass_iner_z,
        #                                np.ones((num_elem,),)*pos_cg_B])
        # self.create_stiff_db_from_vector(np.ones((num_elem,),)*EA,
        #                                 np.ones((num_elem,),)*GAy,
        #                                 np.ones((num_elem,),)*GAz,
        #                                 np.ones((num_elem,),)*GJ,
        #                                 np.ones((num_elem,),)*EIy,
        #                                 np.ones((num_elem,),)*EIz)
        self.create_mass_db_from_vector(np.array([mass_per_unit_length]),
                                       np.array([mass_iner_x]),
                                       np.array([mass_iner_y]),
                                       np.array([mass_iner_z]),
                                       np.array([pos_cg_B]))
        self.create_stiff_db_from_vector(np.array([EA]),
                                        np.array([GAy]),
                                        np.array([GAz]),
                                        np.array([GJ]),
                                        np.array([EIy]),
                                        np.array([EIz]))
        self.create_frame_of_reference_delta(y_BFoR)
        # self.boundary_conditions[-1] = -1
        # self.boundary_conditions[0] = 1


    def assembly_structures(self, *args):
        """
        assembly_structures

        This function concatenates structures to be writen in the same h5 File

        Args:
        	*args: list of StructuralInformation() to be meged into 'self'

        Notes:
        	The structures does NOT merge any node (even if nodes are defined at the same coordinates)

        """

        total_num_beam = max(self.beam_number)+1
        total_num_node = self.num_node
        total_num_elem = self.num_elem
        total_num_stiff = self.stiffness_db.shape[0]
        total_num_mass = self.mass_db.shape[0]

        for structure_to_add in args:
            self.coordinates = np.concatenate((self.coordinates, structure_to_add.coordinates ), axis=0)
            self.connectivities = np.concatenate((self.connectivities, structure_to_add.connectivities + total_num_node), axis=0)
            assert self.num_node_elem == structure_to_add.num_node_elem, "num_node_elem does NOT match"
            self.stiffness_db = np.concatenate((self.stiffness_db, structure_to_add.stiffness_db), axis=0)
            self.elem_stiffness = np.concatenate((self.elem_stiffness, structure_to_add.elem_stiffness + total_num_stiff), axis=0)
            self.mass_db = np.concatenate((self.mass_db, structure_to_add.mass_db), axis=0)
            self.elem_mass = np.concatenate((self.elem_mass, structure_to_add.elem_mass + total_num_mass), axis=0)
            self.frame_of_reference_delta = np.concatenate((self.frame_of_reference_delta, structure_to_add.frame_of_reference_delta), axis=0)
            self.structural_twist = np.concatenate((self.structural_twist, structure_to_add.structural_twist), axis=0)
            self.boundary_conditions = np.concatenate((self.boundary_conditions, structure_to_add.boundary_conditions), axis=0)
            self.beam_number = np.concatenate((self.beam_number, structure_to_add.beam_number + total_num_beam), axis=0)
            self.app_forces = np.concatenate((self.app_forces, structure_to_add.app_forces), axis=0)
            # self.body_number = np.concatenate((self.body_number, structure_to_add.body_number), axis=0)
            if not self.lumped_mass_nodes == None:
                self.lumped_mass_nodes  = np.concatenate((self.lumped_mass_nodes, structure_to_add.lumped_mass_nodes + total_num_node), axis=0)
                self.lumped_mass  = np.concatenate((self.lumped_mass, structure_to_add.lumped_mass + len(self.lumped_mass_position)), axis=0)
                self.lumped_mass_inertia  = np.concatenate((self.lumped_mass_inertia, structure_to_add.lumped_mass_inertia), axis=0)
                self.lumped_mass_position  = np.concatenate((self.lumped_mass_position, structure_to_add.lumped_mass_position ), axis=0)

            total_num_stiff += structure_to_add.stiffness_db.shape[0]
            total_num_mass += structure_to_add.mass_db.shape[0]
            total_num_beam += max(structure_to_add.beam_number)
            total_num_node += structure_to_add.num_node
            total_num_elem += structure_to_add.num_elem

        self.num_node = total_num_node
        self.num_elem = total_num_elem

    def check_StructuralInformation(self):
        """
        check_StructuralInformation

        Check some properties of the StructuralInformation()

        Notes:
        	These conditions have to be to correctly define a case but they are not the only ones

        """
        # CHECKING
        if(self.elem_stiffness.shape[0]!=self.num_elem):
            sys.exit("ERROR: Element stiffness must be defined for each element")
        if(self.elem_mass.shape[0]!=self.num_elem):
            sys.exit("ERROR: Element mass must be defined for each element")
        if(self.frame_of_reference_delta.shape[0]!=self.num_elem):
            sys.exit("ERROR: The first dimension of FoR does not match the number of elements")
        if(self.frame_of_reference_delta.shape[1]!=self.num_node_elem):
            sys.exit("ERROR: The second dimension of FoR does not match the number of nodes element")
        if(self.frame_of_reference_delta.shape[2]!=3):
            sys.exit("ERROR: The third dimension of FoR must be 3")
        if(self.structural_twist.shape[0]!=self.num_node):
            sys.exit("ERROR: The structural twist must be defined for each node")
        if(self.boundary_conditions.shape[0]!=self.num_node):
            sys.exit("ERROR: The boundary conditions must be defined for each node")
        if(self.beam_number.shape[0]!=self.num_elem):
            sys.exit("ERROR: The beam number must be defined for each element")
        if(self.app_forces.shape[0]!=self.num_node):
            sys.exit("ERROR: The first dimension of the applied forces matrix does not match the number of nodes")
        if(self.app_forces.shape[1]!=6):
            sys.exit("ERROR: The second dimension of the applied forces matrix must be 6")

    def generate_fem_file(self, route, case_name):
        """
        generate_fem_file

        Writes the h5 file with the structural information

        Args:
        	route (string): path of the case
        	case_name (string): name of the case
        """
    	# TODO: check variables that are not defined

        # Writting the file
        with h5.File(route + '/' + case_name + '.fem.h5', 'a') as h5file:
    		# TODO: include something to write only exsisting variables
            h5file.create_dataset('coordinates', data=self.coordinates)
            h5file.create_dataset('connectivities', data=self.connectivities)
            h5file.create_dataset('num_node_elem', data=self.num_node_elem)
            h5file.create_dataset('num_node', data=self.num_node)
            h5file.create_dataset('num_elem', data=self.num_elem)
            h5file.create_dataset('stiffness_db', data=self.stiffness_db)
            h5file.create_dataset('elem_stiffness', data=self.elem_stiffness)
            h5file.create_dataset('mass_db', data=self.mass_db)
            h5file.create_dataset('elem_mass', data=self.elem_mass)
            h5file.create_dataset('frame_of_reference_delta', data=self.frame_of_reference_delta)
            h5file.create_dataset('structural_twist', data=self.structural_twist)
            h5file.create_dataset('boundary_conditions', data=self.boundary_conditions)
            h5file.create_dataset('beam_number', data=self.beam_number)
            h5file.create_dataset('app_forces', data=self.app_forces)
            # h5file.create_dataset('body_number', data=self.body_number)
            if not self.lumped_mass_nodes is None:
                h5file.create_dataset('lumped_mass_nodes', data=self.lumped_mass_nodes)
                h5file.create_dataset('lumped_mass', data=self.lumped_mass)
                h5file.create_dataset('lumped_mass_inertia', data=self.lumped_mass_inertia)
                h5file.create_dataset('lumped_mass_position', data=self.lumped_mass_position)


######################################################################
###############  BLADE AERODYNAMIC INFORMATION  ######################
######################################################################
class AerodynamicInformation():
    """
    AerodynamicInformation

    Aerodynamic information needed to build a case

    Note:
        It should be defined after the StructuralInformation of the case
    """
    def __init__(self):
        """
        __init__

        Initialization
        """
        self.aero_node = None
        self.chord = None
        self.twist = None
        self.sweep = None
        self.surface_m = None
        self.surface_distribution = None
        self.m_distribution = None
        self.elastic_axis = None
        self.airfoil_distribution = None
        self.airfoils = None
        # TODO: Define the following variables at some point
        # self.control_surface = None
        # self.control_surface_type = None
        # self.control_surface_deflection = None
        # self.control_surface_chord = None
        # self.control_surface_hinge_coords = None

    def copy(self):
        """
        copy

        Returns a copy of the object

        Returns:
        	copied(AerodynamicInformation): new object with the same properties
        """
        copied = AerodynamicInformation()

        copied.aero_node = self.aero_node.astype(dtype=bool, copy=True)
        copied.chord = self.chord.astype(dtype=float, copy=True)
        copied.twist = self.twist.astype(dtype=float, copy=True)
        copied.sweep = self.sweep.astype(dtype=float, copy=True)
        copied.surface_m = self.surface_m.astype(dtype=int, copy=True)
        copied.surface_distribution = self.surface_distribution.astype(dtype=int, copy=True)
        copied.m_distribution = self.m_distribution
        copied.elastic_axis = self.elastic_axis.astype(dtype=float, copy=True)
        copied.airfoil_distribution = self.airfoil_distribution.astype(dtype=int, copy=True)
        copied.airfoils = self.airfoils.astype(dtype=float, copy=True)

        return copied

    def set_to_zero(self, num_node_elem, num_node, num_elem,
                    num_airfoils = 1, num_surfaces = 0, num_points_camber = 100):
        """
        set_to_zero

        Sets to zero all the variables

        Args:
            num_node_elem (int): number of nodes per element
            num_node (int): number of nodes
            num_elem (int): number of elements
            num_airfoils (int): number of different airfoils
            num_surfaces (int): number of aerodynamic surfaces
            num_points_camber (int): number of points to define the camber line of the airfoil
        """
        self.aero_node = np.zeros((num_node,), dtype = bool)
        self.chord = np.zeros((num_elem,num_node_elem), dtype = float)
        self.twist = np.zeros((num_elem,num_node_elem), dtype = float)
        self.sweep = np.zeros((num_elem,num_node_elem), dtype = float)
        # TODO: SHARPy does not ignore the surface_m when the surface is not aerodynamic
        #self.surface_m = np.array([0], dtype = int)
        self.surface_m = np.array([], dtype=int)
        self.surface_distribution = np.zeros((num_elem,), dtype=int) - 1
        self.m_distribution = 'uniform'
        self.elastic_axis = np.zeros((num_elem,num_node_elem), dtype = float)
        self.airfoil_distribution = np.zeros((num_elem,num_node_elem), dtype=int)
        self.airfoils = np.zeros((num_airfoils,num_points_camber,2), dtype = float)
        for iairfoil in range(num_airfoils):
            self.airfoils[iairfoil,:,0] = np.linspace(0.0, 1.0, num_points_camber)

    def generate_full_aerodynamics(self,
                                   aero_node,
                                   chord,
                                   twist,
                                   sweep,
                                   surface_m,
                                   surface_distribution,
                                   m_distribution,
                                   elastic_axis,
                                   airfoil_distribution,
                                   airfoils):
        """
        generate_full_aerodynamics

        Defines the whole case from the appropiated variables

        Args:
        	aero_node (np.array): defines if a node has aerodynamic properties or not
            chord (np.array): chord of the elements
            twist (np.array): twist of the elements
            sweep (np.array): sweep of the elements
            surface_m (np.array): Number of panels in the chord direction
            surface_distribution (np.array): Surface at which each element belongs
            m_distribution (str): distribution of the panels along the chord
            elastic_axis (np.array): position of the elastic axis in the chord
            airfoil_distribution (np.array): airfoil at each element node
            airfoils (np.array): coordinates of the camber lines of the airfoils
        """

        self.aero_node = aero_node
        self.chord = chord
        self.twist = twist
        self.sweep = sweep
        self.surface_m = surface_m
        self.surface_distribution = surface_distribution
        self.m_distribution = m_distribution
        self.elastic_axis = elastic_axis
        self.airfoil_distribution = airfoil_distribution
        self.airfoils = airfoils

    def create_aerodynamics_from_vec(self,
                                     StructuralInformation,
                                     vec_aero_node,
                                     vec_chord,
                                     vec_twist,
                                     vec_sweep,
                                     vec_surface_m,
                                     vec_surface_distribution,
                                     vec_m_distribution,
                                     vec_elastic_axis,
                                     vec_airfoil_distribution,
                                     airfoils):
        """
        create_aerodynamics_from_vec

        Defines the whole case from the appropiated variables in vector form (associated to nodes)

        Args:
            StructuralInformation (StructuralInformation): Structural infromation of the case
        	vec_aero_node (np.array): defines if a node has aerodynamic properties or not
            vec_chord (np.array): chord of the nodes
            vec_twist (np.array): twist of the nodes
            vec_sweep (np.array): sweep of the nodes
            vec_surface_m (np.array): Number of panels in the chord direction
            vec_surface_distribution (np.array): Surface at which each element belongs
            vec_m_distribution (np.array): distribution of the panels along the chord
            vec_elastic_axis (np.array): position of the elastic axis in the chord
            vec_airfoil_distribution (np.array): airfoil at each element node
            airfoils (np.array): coordinates of the camber lines of the airfoils
        """
        self.aero_node = vec_aero_node

        self.chord = from_node_list_to_elem_matrix(vec_chord, StructuralInformation.connectivities)
        self.twist = from_node_list_to_elem_matrix(vec_twist, StructuralInformation.connectivities)
        self.sweep = from_node_list_to_elem_matrix(vec_sweep, StructuralInformation.connectivities)
        self.elastic_axis = from_node_list_to_elem_matrix(vec_elastic_axis, StructuralInformation.connectivities)
        self.airfoil_distribution = from_node_list_to_elem_matrix(vec_airfoil_distribution, StructuralInformation.connectivities)

        self.surface_m = vec_surface_m
        self.surface_distribution = vec_surface_distribution
        self.m_distribution = vec_m_distribution

        self.airfoils = airfoils

    def create_one_uniform_aerodynamics(self,
                                     StructuralInformation,
                                     chord,
                                     twist,
                                     sweep,
                                     surface_m,
                                     m_distribution,
                                     elastic_axis,
                                     airfoil):
        """
        create_one_uniform_aerodynamics

        Defines the whole case from the appropiated variables constant at every point

        Args:
            StructuralInformation (StructuralInformation): Structural infromation of the case
            chord (float): chord
            twist (float): twist
            sweep (float): sweep
            surface_m (int): Number of panels in the chord direction
            m_distribution (str): distribution of the panels along the chord
            elastic_axis (float): position of the elastic axis in the chord
            airfoils (np.array): coordinates of the camber lines of the airfoils
        """
        num_node = StructuralInformation.num_node
        num_node_elem = StructuralInformation.num_node_elem
        num_elem = StructuralInformation.num_elem

        self.aero_node = np.ones((num_node,), dtype = bool)
        self.chord = chord*np.ones((num_elem,num_node_elem), dtype = float)
        self.twist = twist*np.ones((num_elem,num_node_elem), dtype = float)
        self.sweep = sweep*np.ones((num_elem,num_node_elem), dtype = float)
        # TODO: SHARPy does not ignore the surface_m when the surface is not aerodynamic
        #self.surface_m = np.array([0], dtype = int)
        self.surface_m = np.array([0], dtype=int)
        self.surface_distribution = np.zeros((num_elem,), dtype=int) - 1
        self.m_distribution = m_distribution
        self.elastic_axis = elastic_axis*np.ones((num_elem,num_node_elem), dtype = float)
        self.airfoil_distribution = np.ones((num_elem,num_node_elem), dtype=int)
        self.airfoils = np.zeros((1,num_points_camber,2), dtype = float)
        self.airfoil = airfoil

    def assembly_aerodynamics(self, *args):
        """
        assembly_aerodynamics

        This function concatenates aerodynamic properties to be writen in the same h5 File

        Args:
        	*args: list of AerodynamicInformation() to be meged into 'self'
        """

        total_num_airfoils = self.num_airfoils
        total_num_surfaces = self.num_surfaces
        # TODO: check why I only need one definition of m and not one per surface

        for aerodynamics_to_add in args:
            self.chord = np.concatenate((self.chord, aerodynamics_to_add.chord), axis=0)
            self.aerodynamic_twist = np.concatenate((self.aerodynamic_twist, aerodynamics_to_add.aerodynamic_twist), axis=0)
            self.surface_m = np.concatenate((self.surface_m, aerodynamics_to_add.surface_m), axis=0)
            #self.m_distribution.append(aerodynamics_to_add.m_distribution)
            assert self.m_distribution == aerodynamics_to_add.m_distribution, "m_distribution does not match"
            self.surface_distribution = np.concatenate((self.surface_distribution, aerodynamics_to_add.surface_distribution + total_num_surfaces), axis=0)
            self.aero_node = np.concatenate((self.aero_node, aerodynamics_to_add.aero_node), axis=0)
            self.elastic_axis = np.concatenate((self.elastic_axis, aerodynamics_to_add.elastic_axis), axis=0)
            # np.concatenate((self.airfoil_distribution, aerodynamics_to_add.airfoil_distribution), axis=0)
            self.airfoil_distribution = np.concatenate((self.airfoil_distribution, aerodynamics_to_add.airfoil_distribution + total_num_airfoils), axis=0)
            self.airfoils = np.concatenate((self.airfoils, aerodynamics_to_add.airfoils), axis=0)

            total_num_airfoils += aerodynamics_to_add.num_airfoils
            total_num_surfaces += aerodynamics_to_add.num_surfaces

        self.num_airfoils = total_num_airfoils
        self.num_surfaces = total_num_surfaces

    def interpolate_airfoils_camber(self, pure_airfoils_camber, r_pure_airfoils, r):
        """
        interpolate_airfoils_camber

        Create the camber of the airfoil at each node position from the camber of the
        pure airfoils present in the blade

        Args:
            pure_airfoils_camber (np.array): xy coordinates of the camber lines of the pure airfoils
            r_pure_airfoils (np.array): radial position of the pure airfoils
            r (np.array): radial positions to compute the camber lines through linear interpolation

        Returns:
        	airfoils_camber (np.array): camber lines at the new radial positions

        """
        num_node = len(r)
        airfoils_camber = np.zeros((num_node,self.n_points_camber,2),)

        for inode in range(num_node):
            # camber_x, camber_y = get_airfoil_camber(x,y)

            iairfoil=0
            while(r[inode]<r_pure_airfoils[iairfoil]):
                iairfoil+=1
                if(iairfoil==len(r_pure_airfoils)):
                    iairfoil-=1
                    break

            beta=min((r[inode]-r_pure_airfoils[iairfoil-1])/(r_pure_airfoils[iairfoil]-r_pure_airfoils[iairfoil-1]),1.0)
            beta=max(0.0,beta)

            airfoils_camber[inode,:,0]=(1-beta)*pure_airfoils_camber[iairfoil-1,:,0]+beta*pure_airfoils_camber[iairfoil,:,0]
            airfoils_camber[inode,:,1]=(1-beta)*pure_airfoils_camber[iairfoil-1,:,1]+beta*pure_airfoils_camber[iairfoil,:,1]

        return airfoils_camber

    def check_AerodynamicInformation(self, StructuralInformation):
        """
        check_AerodynamicInformation

        Check some properties of the AerodynamicInformation()

        Notes:
            These conditions have to be to correctly define a case but they are not the only ones

        """
        # CHECKING
        if(self.aero_node.shape[0] != StructuralInformation.num_node):
            sys.exit("ERROR: Aero node must be defined for each node")
        if(self.airfoil_distribution.shape[0] != StructuralInformation.num_elem or self.airfoil_distribution.shape[1]!=StructuralInformation.num_node_elem):
            sys.exit("ERROR: Airfoil distribution must be defined for each element/local node")
        if(self.chord.shape[0] != StructuralInformation.num_elem):
            sys.exit("ERROR: The first dimension of the chord matrix does not match the number of elements")
        if(self.chord.shape[1] != StructuralInformation.num_node_elem):
            sys.exit("ERROR: The second dimension of the chord matrix does not match the number of nodes per element")
        if(self.elastic_axis.shape[0] != StructuralInformation.num_elem):
            sys.exit("ERROR: The first dimension of the elastic axis matrix does not match the number of elements")
        if(self.elastic_axis.shape[1] != StructuralInformation.num_node_elem):
            sys.exit("ERROR: The second dimension of the elastic axis matrix does not match the number of nodes per element")
        if(self.surface_distribution.shape[0] != StructuralInformation.num_elem):
            sys.exit("ERROR: The surface distribution must be defined for each element")
        if(self.aerodynamic_twist.shape[0] != StructuralInformation.num_elem):
            sys.exit("ERROR: The first dimension of the aerodynamic twist does not match the number of elements")
        if(self.aerodynamic_twist.shape[1] != StructuralInformation.num_node_elem):
            sys.exit("ERROR: The second dimension of the aerodynamic twist does not match the number nodes per element")

    def generate_aero_file(self, route, case_name):
        """
        generate_aero_file

        Writes the h5 file with the aerodynamic information

        Args:
            route (string): path of the case
            case_name (string): name of the case
        """
        with h5.File(route + '/' + case_name + '.aero.h5', 'a') as h5file:

            h5file.create_dataset('aero_node', data=self.aero_node)
            chord_input = h5file.create_dataset('chord', data=self.chord)
            chord_input .attrs['units'] = 'm'
            twist_input = h5file.create_dataset('twist', data=self.aerodynamic_twist)
            twist_input.attrs['units'] = 'rad'
            h5file.create_dataset('surface_m', data=self.surface_m)
            h5file.create_dataset('surface_distribution', data=self.surface_distribution)
            h5file.create_dataset('m_distribution', data=self.m_distribution.encode('ascii', 'ignore'))
            h5file.create_dataset('elastic_axis', data=self.elastic_axis)
            h5file.create_dataset('airfoil_distribution', data=self.airfoil_distribution)

            airfoils_group = h5file.create_group('airfoils')
            for iairfoil in range(len(self.airfoils)):
                airfoils_group.create_dataset("%d" % iairfoil, data=self.airfoils[iairfoil,:,:])

            #control_surface_input = h5file.create_dataset('control_surface', data=control_surface)
            #control_surface_deflection_input = h5file.create_dataset('control_surface_deflection', data=control_surface_deflection)
            #control_surface_chord_input = h5file.create_dataset('control_surface_chord', data=control_surface_chord)
            #control_surface_types_input = h5file.create_dataset('control_surface_type', data=control_surface_type)

######################################################################
###############  BLADE AEROELASTIC INFORMATION  ######################
######################################################################
class AeroelasticInformation():
    """
    AeroelasticInformation

    Structural and aerodynamic information needed to build a case
    """
    def __init__(self):
        """
        __init__

        Initialization
        """
        self.StructuralInformation = StructuralInformation()
        self.AerodynamicInformation = AerodynamicInformation()

    def generate(self, StructuralInformation, AerodynamicInformation):
        """
        generate

        Generates an object from the structural and the aerodynamic information

        Args:
            StructuralInformation (StructuralInformation): structural information
            AerodynamicInformation (AerodynamicInformation): aerodynamic information
        """
        self.StructuralInformation = StructuralInformation.copy()
        self.AerodynamicInformation = AerodynamicInformation.copy()

    def assembly(self, *args):
        """
        assembly

        This function concatenates structures and aerodynamic properties to be writen in the same h5 File

        Args:
        	*args: list of AeroelasticInformation() to be meged into 'self'

        Notes:
        """
        list_of_SI = []
        list_of_AI = []

        for AEI in args:
            list_of_SI.append(AEI.StructuralInformation)
            list_of_AI.append(AEI.AerodynamicInformation)

        self.StructuralInformation.assembly_structures(*list_of_SI)
        self.AerodynamicInformation.assembly_aerodynamics(*list_of_AI)

    def remove_duplicated_points(self, tol):
        """
        Algebra Function Title

        Short description

        Longer description

        Args:
        	arg1 (float): arg1 description
        	arg2 (float): arg2 description

        Returns:
        	float: function return descritpion

        Examples:

        Notes:
        	Here you can have specifics and math descriptions.
        	To enter math mode simply write
        	.. math:: e^{i\\pi} + 1 = 0
        	Math mode supports TeX sintax but note that you should use two backslashes \\ instead of one.
        	Sphinx supports reStructuredText should you want to format text...

        """

        def find_connectivities_index(connectivities, iprev_node):

            found = False
            for icon in range(connectivities.shape[0]):
                for jcon in range(connectivities.shape[1]):
                    if connectivities[icon2, jcon2] == iprev_node:
                        found = True
                        break
                if found:
                    break

            return icon, jcon

        inode = 1
        while inode < self.StructuralInformation.num_nodes:
            # Check if the current node is close to any of the previous ones
            replace = False
            for iprev_node in range(inode):
                if np.linalg.norm(self.StructuralInformation.coordinates[inode,:]-self.StructuralInformation.coordinates[iprev_node,:]) < tol:
                    replace = True
                    break

            if replace:
                self.coordinates = np.delete(self.coordinates, (inode), axis=0)
                self.elem_stiffness = np.delete(self.elem_stiffness, (inode), axis=0)
                self.elem_mass = np.delete(self.elem_mass, (inode), axis=0)
                self.structural_twist = np.delete(self.structural_twist, (inode), axis=0)
                self.boundary_conditions = np.delete(self.boundary_conditions, (inode), axis=0)
                self.beam_number = np.delete(self.beam_number, (inode), axis=0)
                self.app_forces = np.delete(self.app_forces, (inode), axis=0)
                self.frame_of_reference_delta = np.delete(self.frame_of_reference_delta, (inode), axis=0)

                self.AerodynamicInformation.aero_node = np.delete(self.AerodynamicInformation.aero_node, (inode), axis=0)

                if not self.lumped_mass_nodes is None:
                    for ilumped in range(len(self.lumped_mass_nodes)):
                        if self.lumped_mass_nodes[ilumped] == inode:
                            self.lumped_mass_nodes = np.delete(self.lumped_mass_nodes, (inode), axis=0)
                            self.lumped_mass = np.delete(self.lumped_mass, (inode), axis=0)
                            self.lumped_mass_inertia = np.delete(self.lumped_mass_inertia, (inode), axis=0)
                            self.lumped_mass_position = np.delete(self.lumped_mass_position, (inode), axis=0)

                for icon in range(connectivities.shape[0]):
                    for jcon in range(connectivities.shape[1]):
                        if connectivities[icon,jcon] == inode:
                            icon_prev, jcon_prev = find_connectivities_index(connectivities, iprev_node):
                            self.AerodynamicInformation.chord[icon, jcon] = self.AerodynamicInformation.chord[icon_prev, jcon_prev]
                            connectivities[icon, jcon] = iprev_node
            else:
                inode += 1

    # TODO: I need also to reduce the following values in connectivities, and change inode inode_prev accordingly for future loops

    def copy(self):
        """
        copy

        Returns a copy of the object

        Returns:
        	copied(AeroelasticInformation): new object with the same properties
        """
        copied = AeroelasticInformation()

        copied.StructuralInformation = self.StructuralInformation.copy()
        copied.AerodynamicInformation = self.AerodynamicInformation.copy()

        return copied

    def write_h5_files(self):
        """
        write_h5_files

        Writes the structural and aerodynamic h5 files
        """
        self.StructuralInformation.generate_fem_file()
        self.AerodynamicInformation.generate_aero_file()

######################################################################
######################  SOLVERS INFORMATION  #########################
######################################################################
class SimulationInformation():
    """
    SimulationInformation

    Simulation information needed to build a case
    """

    def __init__(self):
        """
        __init__

        Initialization
        """
        self.main = dict()
        self.solvers = dict()
        # self.preprocessors = dict()
        self.postprocessors = dict()

        self.with_dynamic_forces = False
        self.dynamic_forces = None
        self.with_forced_vel = False
        self.for_vel = None
        self.for_acc = None

    def set_default_values(self):
        """
        set_default_values

        Set the default values for all the solvers
        """

        self.solvers['AerogridLoader'] = dict()
        self.solvers['BeamLoader'] = dict()

        self.solvers['AerogridPlot'] = dict()
        self.solvers['WriteVariablesTime'] = dict()
        self.solvers['BeamPlot'] = dict()

        self.solvers['NonLinearStatic'] = dict()
        self.solvers['StaticUvlm'] = dict()
        self.solvers['NonLinearDynamicCoupledStep'] = dict()
        self.solvers['NonLinearDynamicMultibody'] = dict()
        self.solvers['StaticCoupled'] = dict()
        self.solvers['DynamicCoupled'] = dict()

        # MAIN
        self['main'] = {'flow': '',
                  'case': 'default_case_name',
                  'route': '',
                  'write_screen': 'on',
                  'write_log': 'off',
                  'log_folder': '',
                  'log_file': 'log'}

        # LOADERS
        self.solvers['BeamLoader'] = {'unsteady': 'off',
                                    'orientation': np.array([1., 0, 0, 0])}

        self.solvers['AerogridLoader'] = {'unsteady': 'off',
                                      'aligned_grid': 'on',
                                      'freestream_dir': ['0.0', '1.0', '0.0'],
                                      'mstar': 10}

        # POSTPROCESSORS
        self.solvers['AerogridPlot'] = {'folder': './output',
                            'include_rbm': 'on',
                            'include_forward_motion': 'off',
                            'include_applied_forces': 'on',
                            'include_unsteady_applied_forces': 'off',
                            'minus_m_star': 0,
                            'name_prefix': '',
                            'u_inf': 0.0,
                            'dt': 0.0}

        self.solvers['WriteVariablesTime'] = {'delimiter': ' ',
                                          'FoR_variables': '',
                                          'FoR_number': np.array([0]),
                                          'structure_variables': '',
                                          'structure_nodes': np.array([-1]),
                                          'aero_panels_variables': '',
                                          'aero_panels_isurf': np.array([0]),
                                          'aero_panels_im': np.array([0]),
                                          'aero_panels_in': np.array([0]),
                                          'aero_nodes_variables': '',
                                          'aero_nodes_isurf': np.array([0]),
                                          'aero_nodes_im': np.array([0]),
                                          'aero_nodes_in': np.array([0])}

        self.solvers['BeamPlot'] = {'folder': './output',
                                            'include_rbm': 'on',
                                            'include_applied_forces': 'on',
                                            'include_applied_moments': 'on',
                                            'name_prefix': '',
                                            'output_rbm': 'on'}

        # STEPS
        self.solvers['NonLinearStatic'] = {'print_info': 'on',
                                       'max_iterations': 100,
                                       'num_load_steps': 5,
                                       'delta_curved': 1e-5,
                                       'gravity_on': 'off',
                                       'gravity': 9.81,
                                       'min_delta': 1e-7}


        self.solvers['StaticUvlm'] = {'print_info': 'on',
                                      'horseshoe': 'off',
                                      'num_cores': 0,
                                      'n_rollup': 1,
                                      'rollup_dt': 0.1,
                                      'rollup_aic_refresh': 1,
                                      'rollup_tolerance': 1e-4,
                                      'iterative_solver': 'off',
                                      'iterative_tol': 1e-4,
                                      'iterative_precond': 'off',
                                      'velocity_field_generator': 'SteadyVelocityField',
                                      'velocity_field_input': dict(),
                                      'rho': 1.225}

        self.solvers['NonLinearDynamicCoupledStep'] = {'print_info': 'on',
                                                   'max_iterations': 100,
                                                   'num_load_steps': 5,
                                                   'delta_curved': 1e-5,
                                                   'min_delta': 1e-5,
                                                   'newmark_damp': 1e-4,
                                                   'dt': 0.01,
                                                   'num_steps': 500,
                                                   'gravity_on': 'off',
                                                   'gravity': 9.81,
                                                   'initial_velocity_direction': np.array([-1.0, 0.0, 0.0]),
                                                   'initial_velocity': 0}

        self.solvers['NonLinearDynamicMultibody'] = {'print_info': 'on',
                                                   'max_iterations': 100,
                                                   'num_load_steps': 5,
                                                   'delta_curved': 1e-5,
                                                   'min_delta': 1e-5,
                                                   'newmark_damp': 1e-4,
                                                   'dt': 0.01,
                                                   'num_steps': 500,
                                                   'gravity_on': 'off',
                                                   'gravity': 9.81,
                                                   'initial_velocity_direction': np.array([-1.0, 0.0, 0.0]),
                                                   'initial_velocity': 0}

        self.solvers['StepUvlm'] = {'print_info': 'on',
                                    'num_cores': 0,
                                    'n_time_steps': 100,
                                    'convection_scheme': 3,
                                    'dt': 0.1,
                                    'iterative_solver': 'off',
                                    'iterative_tol': 1e-4,
                                    'iterative_precond': 'off',
                                    'velocity_field_generator': 'SteadyVelocityField',
                                    'velocity_field_input': dict(),
                                    'rho': 1.225}

        # COUPLED
        self.solvers['StaticCoupled'] = {'print_info': 'on',
                                     'structural_solver': 'TO BE DEFINED',
                                     'structural_solver_settings': dict(),
                                     'aero_solver':'TO BE DEFINED',
                                     'aero_solver_settings': dict(),
                                     'max_iter': 100,
                                     'n_load_steps': 1,
                                     'tolerance': 1e-5,
                                     'relaxation_factor': 0}

        self.solvers["DynamicCoupled"] = {  'print_info': 'on',
                                            'structural_solver': 'TO BE DEFINED',
                                            'structural_solver_settings': dict(),
                                            'aero_solver': 'TO BE DEFINED',
                                            'aero_solver_settings': dict(),
                                            'n_time_steps': 100,
                                            'dt': 0.05,
                                            'structural_substeps': 1,
                                            'fsi_substeps': 70,
                                            'fsi_tolerance': 1e-5,
                                            'relaxation_factor': 0.2,
                                            'final_relaxation_factor': 0.0,
                                            'minimum_steps': 3,
                                            'relaxation_steps': 100,
                                            'dynamic_relaxation': 'on',
                                            'post_processors': list(),
                                            'post_processor_settings': dict(),
                                            'cleanup_previous_solution': 'on',
                                            'include_unsteady_force_contribution': 'off'}

    def set_variable_all_dicts(self, variable, value):
        """
        set_variable_all_dicts

        Defines the value of a variable in all the available solvers

        Args:
        	variable (str): variable name
        	value ( ): value
        """
        for solver in self.solvers:
            if variable in self.solvers[solver]:
                self.solvers[solver][variable] = value

    def generate_solver_file(self, route, case_name):
        """
        generate_solver_file

        Generates the solver file

        Args:
        	route (string): path of the case
        	case_name (string): name of the case
        """
        import configobj
        config = configobj.ConfigObj()
        config.filename = route + '/' + case_name + '.solver.txt'
        for k, v in self.main.items():
            config[k] = v
        # Loop through the solvers defined in "flow" and write them
        for solver in self.main['flow']:
            config[solver] = self.solvers[solver]
        config.write()

    def generate_dyn_file(self, route, case_name, num_steps):
        """
        generate_dyn_file

        Generates the dynamic file

        Args:
            route (string): path of the case
            case_name (string): name of the case
            num_steps (int): number of steps
        """
        with h5.File(route + '/' + case_name + '.dyn.h5', 'a') as h5file:
            if self.with_dynamic_forces:
                h5file.create_dataset(
                    'dynamic_forces', data=self.dynamic_forces)
            if self.with_forced_vel:
                # TODO: check coherence velocity-acceleration
                h5file.create_dataset(
                    'for_vel', data=self.for_vel)
                h5file.create_dataset(
                    'for_acc', data=self.for_acc)
            h5file.create_dataset(
                'num_steps', data=num_steps)


######################################################################
#########################  CLEAN FILES  ##############################
######################################################################

def clean_test_files(route, case_name):
    """
    clean_test_files

    Removes the previous h5 files

    Args:
    	route (string): path of the case
        case_name (string): name of the case

    """
    fem_file_name = route + '/' + case_name + '.fem.h5'
    if os.path.isfile(fem_file_name):
        os.remove(fem_file_name)

    dyn_file_name = route + '/' + case_name + '.dyn.h5'
    if os.path.isfile(dyn_file_name):
        os.remove(dyn_file_name)

    aero_file_name = route + '/' + case_name + '.aero.h5'
    if os.path.isfile(aero_file_name):
        os.remove(aero_file_name)

    lagrange_file_name = route + '/' + case_name + '.mb.h5'
    if os.path.isfile(lagrange_file_name):
        os.remove(lagrange_file_name)

    solver_file_name = route + '/' + case_name + '.solver.txt'
    if os.path.isfile(solver_file_name):
        os.remove(solver_file_name)

    flightcon_file_name = route + '/' + case_name + '.flightcon.txt'
    if os.path.isfile(flightcon_file_name):
        os.remove(flightcon_file_name)