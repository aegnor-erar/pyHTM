'''
Created on Nov 26, 2010

@author: Jason

Numenta docs are (c) Numenta

'''
from carver.htm.cell import Cell
from carver.htm.synapse import Synapse
from carver.htm.config import config
from carver.htm.segment import Segment
import math

#using an exponential average, so AS*old+(1-AS*current) => new
AVG_SCALE = 0.995
BOOST_RATE = 1

class Column(object):
    '''
    Represents a column in an HTM network
    '''
    
    MIN_OVERLAP = 5 #TODO: choose a reasonable number

    def __init__(self, htm, x, y, cellsPerColumn):
        '''
        
        '''
        self.htm = htm
        self.cells = [Cell() for i in xrange(cellsPerColumn)] #@UnusedVariable
        self.overlap = 0
        #synapses on input/proximal dendrites, forced equal for whole column, in equivalent of single segment
        self.segment = Segment(distal=False)
        self.boost = 1
        self.x = x
        self.y = y
        self.dutyCycleMin = 0
        self.dutyCycleActive = 0
        self.dutyCycleOverlap = 0
        self.active = False
        
    def synapses_firing(self):
        return self.segment.synapses_firing()
    
    def increase_permanences(self, byAmount):
        return self.segment.increase_permanences(byAmount)
        
    def get_duty_cycle_active(self):
        newDutyCycle = AVG_SCALE*self.dutyCycleActive
        if self.active:
            newDutyCycle += (1-AVG_SCALE)
        return newDutyCycle
    
    def get_duty_cycle_overlap(self):
        newDutyCycle = AVG_SCALE*self.dutyCycleOverlap
        if self.overlap > self.MIN_OVERLAP:
            newDutyCycle += (1-AVG_SCALE)
        return newDutyCycle
    
    def next_boost(self):
        if self.dutyCycleActive >= self.dutyCycleMin:
            return 1
        elif self.dutyCycleActive == 0:
            return self.boost * 1.05 #5% growth until you hit something...
        else:
            return self.dutyCycleMin / self.dutyCycleActive
        
    @property
    def synapses(self):
        return self.segment.synapses
        
    @property
    def synapsesConnected(self):
        return self.segment.synapsesConnected
    
    @property
    def neighbors(self):
        return self.htm.neighbors(self)
    
    def bestCell(self):
        '#see htm doc 0.1.1 pg 45: getBestMatchingCell'
        bestCell = None
        bestCellFiringSynapseCount = 0
        
        #find cell with best best matching segment
        for cell in self.cells:
            seg = cell.bestMatchingSegment()
            if seg and len(seg.synapses_firing()) > bestCellFiringSynapseCount:
                bestCellFiringSynapseCount = len(seg.synapses_firing())
                bestCell = cell
            
        #if none, pick the one with the fewest segments
        if bestCell is None:
            fewestSegments = len(self.cells[0].segments)
            bestCell = self.cells[0]
            for cell in self.cells[1:]:
                if len(cell.segments) < fewestSegments:
                    bestCell = cell
                    fewestSegments = len(cell.segments)
            
        return bestCell
    
    def distance_to(self, x, y):
        #map column's x,y values to input space:
        inputx = self.htm.inputCompression * self.x
        inputy = self.htm.inputCompression * self.y
        
        #assume 2d distances for now
        return math.sqrt((x-inputx)**2 + (y-inputy)**2)
    
    def __str__(self):
        #TODO: much more
        return "pos %s,%s; active? %s\n\t%s" % (self.x, self.y, self.active, self.segment)
    
    def neighbor_duty_cycle_max(self):
        '''
        (Adapted from maxDutyCycle)
        Numenta docs: Returns the maximum active duty cycle of the columns in the 
        neighborhood  
        '''
        return max((c.dutyCycleActive for c in self.neighbors))
    
    def kth_neighbor(self, k):
        '''
        
        Numenta docs: Given the list of columns, return the kth highest overlap value
        '''
        allNeighbors = sorted(self.neighbors, key=lambda col: col.overlap)
        index = min(k-1,len(allNeighbors)-1)
        return allNeighbors[index]
    
    def __eq__(self, another):
        if not hasattr(another, 'htm') or not hasattr(another, 'x') or \
            not hasattr(another, 'y') or not hasattr(another, 'boost'):
            return False
        return self.htm == another.htm and self.x == another.x and self.y == another.y
