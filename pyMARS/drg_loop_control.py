from create_trimmed_model import trim
from autoignition_loop_control import autoignition_loop_control
from get_rate_data_drg import get_rates_drg
from drg import trim_drg
import os
from numpy import genfromtxt
import numpy as np

def drg_loop_control(solution_object, args, stored_error, threshold, done, rate_edge_data):
    """ Controls the trimming and error calculation of a solution with the graph already created using the DRGEP method.   

        Parameters
        ----------
        solution_object : obj
            Cantera solution object
        args : obj
            function arguments object
	stored_error: float singleton
	    The error introduced by the last simulation (to be replaced with this simulation).
        threshold: int
            The threshold value at this point in the iteration.
	done: singleton
	    a singleton boolean value that represnts wether or not more species can be excluded from the graph or not. 
	rate_edge_data: array      
	    A 3D array that holds information from the simulation for calculating DRG interaction coefficients.  

        Returns
        -------
        new_solution_objects : obj
            Cantera solution object That has been reduced.  
        """
    
    target_species = args.target                                                

    try:
        os.system('rm mass_fractions.hdf5')
    except Exception:
        pass
    
    #run detailed mechanism and retain initial conditions
    detailed_result = autoignition_loop_control(solution_object, args) #Run simulation
    detailed_result.test.close()
    ignition_delay_detailed = np.array(detailed_result.tau_array)
    species_retained = []
    printout = ''
    print 'Threshold     Species in Mech      Error'
    
    try:
        os.system('rm mass_fractions.hdf5')
    except Exception:
        pass
    
    #run DRG and create new reduced solution
    drgep = trim_drg(rate_edge_data, solution_object, threshold, args.keepers, done,target_species) #Find out what to cut from the model
    exclusion_list = drgep
    new_solution_objects = trim(solution_object, exclusion_list, args.data_file) #Cut the exclusion list from the model.
    species_retained.append(len(new_solution_objects[1].species()))

    #simulated reduced solution
    reduced_result = autoignition_loop_control(new_solution_objects[1], args) #Run simulation on reduced model
    if (reduced_result == 0):
        stored_error[0] = 100
	error = 100
    	printout += str(threshold) + '                 ' + str(len(new_solution_objects[1].species())) + '              '+  str(round(np.max(error), 2)) +'%' + '\n'
    	print printout
        return new_solution_objects
    reduced_result.test.close()
    ignition_delay_reduced = np.array(reduced_result.tau_array)
    
    #Calculate error
    error = (abs(ignition_delay_reduced-ignition_delay_detailed)/ignition_delay_detailed)*100 #Calculate error
    printout += str(threshold) + '                 ' + str(len(new_solution_objects[1].species())) + '              '+  str(round(np.max(error), 2)) +'%' + '\n'
    print printout
    stored_error[0] = round(np.max(error), 2)
   
    #Return new model.  
    new_solution_objects = new_solution_objects[1]
    return new_solution_objects
