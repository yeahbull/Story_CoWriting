#!/usr/bin/env python
# coding: utf-8

"""
library of functions/algorithms to build, update and compaire models of different agents built by a robot.
"""

import numpy as np
from bidict import bidict


""" GLOBAL PARAMETERS """
STIFFNESS = 3
FIRE_TIME = 5
THERSHOLD = 10.
FORGET_RATE = 0.1

""" functions for spiking cascade following distribution of weights"""
#--------------------------------------------------------------------
def stochastic_compare_couples(c1, c2):
    global STIFFNESS
    a,b = c1
    c,d = c2
    s = np.abs(b)**STIFFNESS + np.abs(d)**STIFFNESS
    r = random.uniform(0,s)
    return 1 if r>np.abs(b)**STIFFNESS else -1

def stochastic_compare(x, y):
    s = np.abs(x) + np.abs(y)
    r = random.uniform(0,s)
    return 1 if r>np.abs(x) else -1

def random_pull_list(distribution): # dist. is a list of values
    if distribution:
        couples = zip(range(len(distribution)),distribution)
        sorted_couples = sorted(couples,cmp=stochastic_compare_couples)
        return sorted_couples[0][0], sorted_couples[0][1]
    else:
        return None

def random_pull_dict(distribution): # dist. is a dictionnary key->value
     if distribution:
         sorted_dist = sorted(distribution.items(), key=operator.itemgetter(1), cmp=stochastic_compare_dict)
         return sorted_dist[0][0]
     else:
         return None


""" functions for updating and using list of activated cells """
#--------------------------------------------------------------
def add_activated(activated, cell):
    for i in range(len(activated)-1):
        activated[i] = activated[i+1]
    activated[-1] = cell


""" object Model """
#-------------------
class Model:
    """ an object 'Model' representing hebbian-inspired network that encode dynamics between cells representing concepts learned by an agent."""
    def __init__(self, network=None, activateds=None, modifieds=None):

        global FIRE_TIME

        # DEFAULT:
        self.intensities = {} # list of cell's intensity between -1 and 1 (intensity or truth)
        self.nb_cells = 0
        self.activateds = [] # list of activated cells, the first is the most recently activated (contains by default the cell encoding the empty concept)
        self.modifieds = set() # for each input from exterior (percept or reflex) cell intensities are modified once
                               # it makes the differrence between the flow of thought and real perception
        self.cell_number = bidict() # each cell is numeroted {cell_id <--> cell_number}
        self.counts = np.zeros([0,0]) # count the close activations for hebbian learning
        self.times = np.zeros([0,0]) # count the average delay between two close activations
        self.weights = np.zeros([FIRE_TIME,0,0]) # weights of connexion between cells for different possible (interger) delays

        # network:= [intensities , counts, times, weights]

        # FILLING:
        if network:
            self.intensities = network[0]
            self.nb_cells = len(self.intensities)

            counts = network[1]
            times = network[2]
            weights = network[3]

            if (counts.shape==times.shape) and (times.shape==weights.shape) and (times.shape==(self.nb_cells,self.nb_cells)):
                self.counts = counts
                self.times = times
                self.weights = weights
            else:
                print "Error of dimension in the loaded network !"
                print "Default = np.zeros array"
                self.counts = np.zeros([self.nb_cells,self.nb_cells])
                self.times = np.zeros([self.nb_cells,self.nb_cells])
                self.weights = np.zeros([FIRE_TIME,self.nb_cells,self.nb_cells])

        if activateds:
            self.activateds = activateds

        if modifieds:
            self.modifieds = modifieds


    def __add__(self,cells_id):
        if isinstance(cells_id, list) or isinstance(cells_id, tuple):
            number = self.nb_cells+1
            for cell_id in cells_id:
                self.intensities.setdefault(cell_id,0)
                if cell_id not in self.cell_number:
                    self.cell_number[cell_id] = number
                    number += 1

            new_counts = np.zeros([number, number])
            new_counts[:self.nb_cells,:self.nb_cells] = self.counts
            self.counts = new_counts

            new_times = np.zeros([number, number])
            new_times[:self.nb_cells,:self.nb_cells] = self.times
            self.times = new_times

            new_weigths = np.zeros([number, number])
            new_weights[:self.nb_cells,:self.nb_cells] = self.weights
            self.weights = new_weights

            self.nb_cells = number


    def update(self, percepts=None, reflexes=None):

        # FIND THE NEXT ACTIVATED:
        elligibles = {}
        new_intensities = {}

        # following weights: (no preference for different delays for the moment)
        delay = 0
        for activated in self.activateds:
            intensity = self.intensities[activated]
            weights_to_sons = self.weights[delay][self.cell_number[activated]][:]
            next_id, strength = random_pull_list(intensity*weights_to_sons)

            elligibles.setdefault(next_id,0)
            elligibles[next_id] += np.abs(strength)

            new_intensities.setdefault(next_id,0)
            new_intensities[next_id] += strength - np.abs(strength)*intensity[next_id]
            delay += 1

        # because recently activated:
        for activated in self.activated[-1]:
            elligibles.setdefault(activated,0)
            elligibles[activated] += 0.5 # arbitrary value, should be a global value

            new_intensities.setdefault(next_id,0)
            new_intensities[next_id] += 0.5*(1 - intensity[next_id])

        # because perception:
        if percepts:
            for percept in percepts:
                elligibles.setdefault(percept,0)
                elligibles[percept] += 1. # arbitrary ~ how I trust my perception

                new_intensities.setdefault(next_id,0)
                new_intensities[next_id] += 1*(1 - intensity[next_id])

        # because very important percept:
        if reflexes:
            for reflex in reflexes:
                elligibles.setdefault(reflex,0)
                elligibles[reflex] += 10. # arbitrary

                new_intensities.setdefault(next_id,0)
                new_intensities[next_id] += 1*(1 - intensity[next_id]) # 1 is the max in order to stay btween -1 and 1

        # stochastic election and hebbian reinforcement:
        next_activated = random_pull_dict(elligibles)
        if (next_activated in reflexes) or (next_activated in percepts):
            self.modifieds = set()
            delay = 0
            for activated in self.activateds:
                correlation = self.intensitie[next_activated] * self.intensities[activated]
                self.reinforce(activated,next_activated,delay,correlation)
                delay += 1
        add_activated(self.activateds,next_activated)

        # new intensities:
        for cell in new_intensities:
            if cell not in self.modifieds:
                intensities[cell] = new_intensities[cell]
                self.modifieds.add(cell)


    def reinforce(self, cell1, cell2, delay, correlation):

        global THERSHOLD
        global FORGET_RATE

        num_cell1 = self.cell_number[cell1]
        num_cell2 = self.cell_number[cell2]

        n = self.counts[num_cell1][num_cell2]
        t = self.times[num_cell1][num_cell2]

        z = FORGET_RATE*np.sum(self.counts[num_cell1][:])
        self.counts[num_cell1][:] -= z

        if self.counts[num_cell1][num_cell2]+z+1 > THRESHOLD:
            self.counts[num_cell1][num_cell2] += z
        else:
            self.counts[num_cell1][num_cell2] += z+1

        self.times[num_cell1][num_cell2] = (n*t + delay)/(n+1.) # iterative computation of average delay

        if self.counts[num_cell1][num_cell2]>=THRESHOLD: # thist trheshold could be smaller than the other one
            self.weights[delay] += correlation - np.abs(correlation)*self.weights[delay]





