# coding: utf-8 

import sigsim

class Drone :

    def __init__(self, model_order):
        self.K0            = None
        self.T0            = None
        self.dt            = None
        self.input_signal  = None
        #self.output_signal = sigsim.Computed(lambda me : self.K0/self.T0*self.input_signal[0]-1/self.T0*me[model_order], model_order+1, model_order+1)    # explicit scheme
        self.output_signal = sigsim.Computed(lambda me : (me[model_order]+self.dt*self.K0/self.T0*self.input_signal[0])/(1+self.dt/self.T0), model_order, model_order)    # implicit scheme

    def clear(self):
        self.output_signal.clear()

    def next(self, dt):
        self.output_signal.next(dt)
        self.output_signal_delayed.next(dt)

    def set_delay(self, delay) :
        self.output_signal_delay = delay
        self.output_signal_delayed = sigsim.Delayed(self.output_signal, self.output_signal_delay)

class Regulator :

    def __init__(self):
        self.K                     = None
        self.Ti                    = None
        self.Td                    = None
        self.input_signal          = None
        #self.formated_input_signal = sigsim.Smoothed(lambda me : self.input_signal[0], 1, 2, 4, 0.4)
        self.formated_input_signal = sigsim.Computed(lambda me : self.input_signal[0], 1, 2)
        self.output_signal         = sigsim.Computed(lambda me : self.K*(self.formated_input_signal[1]+self.formated_input_signal[0]/self.Ti+self.formated_input_signal[2]*self.Td), 0, 0)

    def clear(self):
        self.output_signal.clear()

    def next(self, dt):
        self.formated_input_signal.next(dt)
        self.output_signal.next(dt)


class SmithPredictorCmdVel :

    def __init__(self, model_order):
        self.input_signal                  = None
        self.drone_simulation              = Drone(model_order)
        self.regulator                     = Regulator()
        self.drone_simulation.input_signal = self.regulator.output_signal
        self.smith_error                   = sigsim.Computed(lambda me : self.input_signal[0]-self.drone_simulation.output_signal[0]+self.drone_simulation.output_signal_delayed[0], 0, 0)
        self.regulator.input_signal        = self.smith_error

    def set_delay(self, delay) :
        self.drone_simulation.set_delay(delay)

    def clear(self):
        self.drone_simulation.clear()
        self.regulator.clear()
        
    def next(self, dt):
        """
           
           input_signal has to be updated externally beforehand.

        """
        self.smith_error.next(dt)
        self.regulator.next(dt)
        self.drone_simulation.next(dt)





        
if __name__ == "__main__":

    import matplotlib.pyplot as plt
    import numpy             as np
    from   random            import random

    axis = input("axis = 'linX', 'linY', 'linZ' or 'angZ'\n")
    
    ### Parameters ###

    if axis == 'linX' or axis == 'linY':
    
        tau         = 0.22
        K0          = 3.0
        T0          = 0.13
        K           = 0.2
        Ti          = 20
        Td          = 14
        dt          = 0.01
        model_order = 2

    elif axis == 'linZ':
        tau         = 0.20
        K0          = 1.0
        T0          = 0.16
        K           = 6
        Ti          = 20
        Td          = 0.2
        dt          = 0.01
        model_order = 1

    elif axis == 'angZ':
        tau         = None
        K0          = None
        T0          = None
        K           = None
        Ti          = None
        Td          = None
        dt          = None
        model_order = 1

    ### Define the blocks ###

    noise_ampl = 0.05
    noise      = noise_ampl*(2*random()-1)
    target     = sigsim.Forced(lambda t : float(t > 2.0)+noise, 0, 0)
    drone      = Drone(model_order)
    predictor  = SmithPredictorCmdVel(model_order)

    drone.K0                      = 0.9*K0
    drone.T0                      = 1.1*T0
    drone.dt                      = dt
    predictor.drone_simulation.K0 = K0
    predictor.drone_simulation.T0 = T0
    predictor.drone_simulation.dt = dt
    predictor.regulator.K         = K
    predictor.regulator.Ti        = Ti
    predictor.regulator.Td        = Td
    
    drone.input_signal     = predictor.regulator.output_signal
    drone.set_delay(0.22)
    predictor.set_delay(0.22)
    erreur                 = sigsim.Computed(lambda me : target[0]-drone.output_signal_delayed[0], 0, 0)
    predictor.input_signal = erreur

    ### Calculate the signals ###
    
    X                   = np.arange(0,10,dt)
    TARGET              = [target[0]]
    POSITION_SIMULATION = [predictor.drone_simulation.output_signal[0]]
    POSITION            = [drone.output_signal_delayed[0]]
    SMITH_ERROR         = [predictor.smith_error[0]]
    ERROR               = [predictor.input_signal[0]]
    
    for x in X[1:]:
        noise = noise_ampl*(2*random()-1)
        target.next(dt)
        erreur.next(dt)
        predictor.next(dt)
        drone.next(dt)
        POSITION_SIMULATION.append(predictor.drone_simulation.output_signal[0])
        TARGET.append(target[0])
        POSITION.append(drone.output_signal_delayed[0])
        ERROR.append(predictor.input_signal[0])
        SMITH_ERROR.append(predictor.smith_error[0])

    ### Show the signals ###
                                             
    plt.figure()
    plt.ylim(-1,2)
    plt.plot(X, TARGET,              '-',  label = 'cmd_vel' )
    plt.plot(X, POSITION,            '--', label = 'position')
    plt.plot(X, POSITION_SIMULATION, '--', label = 'position_simulation')
    plt.plot(X, SMITH_ERROR,         '.',  label = 'smith_error')
    plt.plot(X, ERROR,               '.',  label = 'error')
    plt.legend()
    plt.show()

    
    
    
    


