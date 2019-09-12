# Unit and other tests
import datetime
import gdal
import numpy as np
import os
import pandas as pd
import pickle
import unittest

from RAiDER.llreader import readLL, getHeights
import RAiDER.util
import RAiDER.delay

class TimeTests(unittest.TestCase):

    #########################################
    # Scenario to use: 
    # 0: single point, fixed data
    # 1: single point, WRF, download DEM 
    # 2: 
    # 3: 
    # 4: Small area, ERAI
    # 5: Small area, WRF, los available
    # 6: Small area, ERA5, early date, Zenith
    # 7: Small area, ERA5, late date, Zenith
    # 8: Small area, ERAI, late date, Zenith
    scenario = 'scenario_0'

    # Zenith or LOS?
    useZen = True
    #########################################

    # load the weather model type and date for the given scenario
    outdir = os.path.join(os.getcwd(),'test')
    basedir = os.path.join(outdir, '{}'.format(scenario))
    lines=[]
    with open(os.path.join(basedir, 'wmtype'), 'r') as f:
        for line in f:
            lines.append(line.strip())
    wmtype = lines[0]
    test_time = datetime.datetime.strptime(lines[1], '%Y%m%d%H%M%S')
    flag = lines[-1]
    test_file = os.path.join(basedir,'weather_model_data.csv')

    # get the data for the scenario
    if flag == 'station_file':
       filename = os.path.join(basedir, 'station_file.txt')
       [lats, lons, latproj, lonproj] = readLL(filename)
    else:
       latfile = os.path.join(basedir, 'lat.rdr')
       lonfile = os.path.join(basedir,'lon.rdr')
       losfile = os.path.join(basedir,'los.rdr')
       [lats, lons] = readLL(latfile, lonfile)

    # DEM
    demfile = os.path.join(basedir,'geom', 'warpedDEM.dem')
    wmLoc = os.path.join(basedir, 'weather_files')
    RAiDER.util.mkdir(wmLoc)
    if os.path.exists(demfile):
        heights = ('dem', demfile)
    else:
        heights = ('download', demfile)

    lats, lons, hgts = getHeights(lats, lons,heights)

    if useZen:
        los = None
    else:
        los = ('los', losfile)

    zref = 15000
    out = '.'

    # load the weather model
    try:
       model_name, wm = RAiDER.util.modelName2Module(wmtype)
       weather = {'type': wm(), 'files': None,
                'name': wmtype}
    except:
       weather = {'type': 'pickle', 'files': os.path.join('test', 'scenario_0', 'pickledWeatherModel.pik'),
                'name': 'pickle'}


    # test error messaging
    #@unittest.skip("skipping full model test until all other unit tests pass")
    def test_tropoSmallArea(self):
        wetDelay, hydroDelay = \
            RAiDER.delay.tropo_delay(self.test_time, self.los, self.lats, self.lons, self.hgts,
                  self.weather, self.wmLoc, self.zref, self.out,
                  parallel=False, verbose = True,
                  download_only = False)
        totalDelayEst = wetDelay+hydroDelay

        # get the true delay from the weather model
        picklefile = os.path.join('test', 'scenario_0', 'pickledWeatherModel.pik')
        with open(picklefile, 'rb') as f:
            wm = pickle.load(f)
        wrf = wm._wet_refractivity[1,1,:]
        hrf = wm._hydrostatic_refractivity[1,1,:]
        zs = wm._zs[1,1,:]
        mask = zs > 2907
        totalDelay = 1e-6*(np.trapz(wrf[mask], zs[mask]) + np.trapz(hrf[mask], zs[mask])) 
        #delayDF = pd.read_csv(self.test_file)
        #totalDelay = np.trapz(delayDF['totalRef'].values, x=delayDF['Z'].values)/1e6
        self.assertTrue(np.abs(totalDelay - totalDelayEst) < 0.001)

def main():
    unittest.main()
   
if __name__=='__main__':

    unittest.main()
