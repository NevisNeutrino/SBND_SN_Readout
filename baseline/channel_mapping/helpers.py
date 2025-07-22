import numpy as np
import pandas as pd

# function to find the start and end coordinates on an APA of a wire given the wire no. & which plane it belongs
def find_coords(plane, wire_no):
    
    if plane=='Y':
        
        h = 3991           # height of each APA

        dx = 3             # distance (mm) b/w wires on Y plane
        x = wire_no*3-dx/2

        return [(x,h),(x,0)]
    
    elif plane=='U':
    
        h = 3991        # height of each APA
        w = 2496*2      # width of each APA

        dx = 3/np.cos(np.pi/3)  # distance in x b/w wires on U/V plane
        dy = 3/np.sin(np.pi/3)  # distance in y b/w wires on U/V plane

        minx = dx/2-(w-dx*832)/2    # distance of first wire from sides of APA
        miny = dy/2-(h-dy*1152)/2   # distance of first wire from bottom/top of APA
        
        # find start coordinates
        if wire_no < 1153:     # side wires
            x0 = 0
            y0 = wire_no*dy - miny
        else:                  # top wires
            x0 = (wire_no-1152)*dx - minx
            y0 = h

        # find end coordinates
        if wire_no < 833:     # wires that end on bottom
            xf = wire_no*dx - minx
            yf = 0
        else:                 # wires that end on the side
            xf = w
            yf = (wire_no-832)*dy - miny  

        return [(x0,y0),(xf,yf)]
    
    elif plane=='V':
    
        h = 3991        # height of each APA
        w = 2496*2      # width of each APA

        dx = 3/np.cos(np.pi/3)  # distance in x b/w wires on U/V plane
        dy = 3/np.sin(np.pi/3)  # distance of first wire from bottom/top of APA

        minx = dx/2-(w-dx*832)/2    # distance of first wire from sides of APA
        miny = dy/2-(h-dy*1152)/2   # distance of first wire from bottom/top of APA

        if wire_no < 833:   # top wires
            x0 = wire_no*dx - minx
            y0 = h
        else:               # side wires
            x0 = w
            y0 = (1985-wire_no)*dy - miny

        if wire_no < 1153:      # wires that end on the side
            xf = 0
            yf = (1153-wire_no)*dy - miny
        else:                  # wires that end on bottom
            xf = (wire_no-1152)*dx - minx
            yf = 0  

        return [(x0,y0),(xf,yf)]

# function that returns a list of strings/tuples with ranges from a list of all values
def find_ranges(array):
    n = len(array)
    sarray = np.sort(array)   # ensure that wires are in order
 
    length = 1
    list = []
     
    for i in range (1, n + 1):
     
        if (i == n or sarray[i] -
            sarray[i - 1] != 1):
        
            if (length == 1):
                list.append(str(sarray[i - length]))
            else:
                temp = (sarray[i - length], sarray[i - 1])
                list.append(temp)
                
            length = 1
        
        else:
            length += 1
    return list

def getrangestr(component):
    ranges = find_ranges(component)
    list = []
    for range in ranges:
        if type(range) == str:
            list.append(str(range))
        elif type(range) == tuple:
            list.append('-'.join(map(str, range)))

    return ' & '.join(list)

def loadchmap(file):
    column_names = ['Wire number', 'Wire plane', 'APA', 'Half', 'Top/Side', 
    'FEMB Position', 'FEMB Serial #', 'FEMB #', 'FEMB ch #', 'ASIC #', 
    'WIB Crate #', 'WIB #', 'WIB ch #', 'WIB QFSP', 'QFSP Fiber #',	
    'Crate #', 'FEM #', 'FEM ch #', 'LArSoft ch #']
    df = pd.read_csv(file, sep=' ', header=None, names=column_names)
    return df

if __name__ == "__main__":
  find_coords('U', 1)
  find_ranges([0,1])
  getrangestr([0,1])
  loadchmap('SBNDTPCChannelMap_v1.txt')
