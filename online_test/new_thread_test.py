from asyncio.events import BaseDefaultEventLoopPolicy
from concurrent.futures import process
from sqlite3 import DatabaseError
from unicodedata import digit
import clr
import ctypes
import numpy as np
from multiprocessing import Process, Manager
import keyboard
from threading import Thread
import time
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
clr.FindAssembly("OlympusNDT.Instrumentation.NET.dll")
clr.AddReference('OlympusNDT.Instrumentation.NET')

from OlympusNDT.Instrumentation.NET import Utilities, IDeviceDiscovery, DiscoverResult, IFirmwarePackageScanner
from OlympusNDT.Instrumentation.NET import UltrasoundTechnology, IAcquisition

velocity = 5900 * 1e-6 ##mm/ns  self defined. for 5900m/s it is steel


# class process_ascan(Thread):
#     def __init__(self):
def process_ascan(result):
    thread_result = result 
    ascan = thread_result.cycleData.GetAscanCollection().GetAscan(0)  #AScan data process
    ascan_ptr = ascan.GetData()
    sample_quantity = ascan.GetSampleQuantity()
    AmplitudeSamplingDataRage_min = ascan.GetAmplitudeSamplingDataRange().GetFloatingMin()
    AmplitudeSamplingDataRage_max = ascan.GetAmplitudeSamplingDataRange().GetFloatingMax()
    # print('Amplitude Sampliding unit:' , ascan.GetAmplitudeSamplingDataRange().GetUnit())  #unit is sample
    AmplitudeSamplingDataRage_resolution = (AmplitudeSamplingDataRage_max-AmplitudeSamplingDataRage_min)/sample_quantity
    AmplitudeDataRange_min = ascan.GetAmplitudeDataRange().GetFloatingMin()
    AmplitudeDataRange_max = ascan.GetAmplitudeDataRange().GetFloatingMax()
    # print("Amplitude Data range Unit: ",ascan.GetAmplitudeDataRange().GetUnit())  #Percent is the unit
    AmplitudeDataRange_resolution = (AmplitudeDataRange_max-AmplitudeDataRange_min) / sample_quantity
    TimeDataRange_min = ascan.GetTimeDataRange().GetFloatingMin()
    TimeDataRange_max = ascan.GetTimeDataRange().GetFloatingMax()
    AscanX_min = TimeDataRange_min * velocity 
    AscanX_max = TimeDataRange_max * velocity
    # print(AscanX_max,AscanX_min, ascan.GetTimeDataRange().GetUnit())  #confirmed to be the nanosecond
    CycleID = thread_result.cycleData.GetCycleId()
    newpnt = ctypes.cast(ascan_ptr.ToInt64(), ctypes.POINTER(ctypes.c_int32))
    DataBytes = np.ctypeslib.as_array(newpnt, (sample_quantity,))  # no internal copy   
    """Raw Data"""
    AScan_multiply_reading = DataBytes * np.array([float(AmplitudeSamplingDataRage_resolution)])   #Convert to percent
    X_axis = np.linspace(AscanX_min,AscanX_max,sample_quantity)  #get the Thickness reading for the X-axis
    # try:
    #     print(CycleID,'Sampling Resol', AmplitudeSamplingDataRage_resolution)
    # except:
    print(CycleID,np.max(DataBytes))
    # """Setup Threshold"""
    # amp_gate_lower_limit = 45
    # Xaxis_lower_limit = 26
    # Xaxis_higher_limit = 120  
    # """Apply gate threshold for both x-axis and amplitude in the ascan"""
    # xaxis_index_processed_arr = np.array(np.where((X_axis > Xaxis_lower_limit) & (X_axis < Xaxis_higher_limit)))[0]
    # amp_index_processed_arr = np.array(np.where(AScan_multiply_reading > amp_gate_lower_limit))
    # overlapping_process_index_arr = np.intersect1d(xaxis_index_processed_arr,amp_index_processed_arr)
    # X_axis_processed = X_axis[overlapping_process_index_arr]
    # amp_axis_processed = AScan_multiply_reading[overlapping_process_index_arr]
    # if (X_axis_processed.size != 0 ) and (amp_axis_processed.size != 0):
    #     the_index = int(((np.where(amp_axis_processed == np.amax(amp_axis_processed)))[0])[0])
    #     # defect_point = [X_axis_processed[the_index],amp_axis_processed[the_index]]
    #     print(f'Cycle ID:{CycleID}, Depth:{X_axis_processed[the_index]}mm, Amplitude{amp_axis_processed[the_index]}%')
    # else:
    #     print(f'Cycle ID:{CycleID}, Sample Quantity: {sample_quantity}')
    
    
    


class FPXDevice(object):
    def __init__(self, ip_address):
        Utilities.ResolveDependenciesPath()
        deviceDiscovery = IDeviceDiscovery.Create(ip_address)
        discoverResult = deviceDiscovery.DiscoverFor(5000)
        self.device = discoverResult.device
        if discoverResult.status == DiscoverResult.Status.DeviceFound:
            print("Focus PX Device is found!")

    def download_firmware_package(self, package_name):
        firmwarePackages = IFirmwarePackageScanner.GetFirmwarePackageCollection()
        for i in range(firmwarePackages.GetCount()):
            fw_name = firmwarePackages.GetFirmwarePackage(i).GetName()
            if fw_name.find(package_name) != -1:
                print("Firmware Package %s is found!" % fw_name)
                firmwarePackage = firmwarePackages.GetFirmwarePackage(i)
                self.device.Start(firmwarePackage)
                print("Firmware Package is started!")
                return

    def create_beamset(self, connector_index):
        deviceConfiguration = self.device.GetConfiguration()
        ultrasoundConfiguration = deviceConfiguration.GetUltrasoundConfiguration()
        digitizerTechnology = ultrasoundConfiguration.GetDigitizerTechnology(UltrasoundTechnology.Conventional)
        beamSetFactory = digitizerTechnology.GetBeamSetFactory()
        beamSet = beamSetFactory.CreateBeamSetConventional("Conventional")
        connector = digitizerTechnology.GetConnectorCollection().GetConnector(connector_index)
        connector_count = digitizerTechnology.GetConnectorCollection().GetCount()
        ultrasoundConfiguration.GetFiringBeamSetCollection().Add(beamSet, connector)

        beam = beamSet.GetBeam(0)
        print(f'AScan Start:{beam.GetAscanStart()}, AScan Length: {beam.GetAscanLength()}')
        self.setup_ascan(beam_set=beam)


    def setup_ascan(self,beam_set):
        beam = self.create_beamset()
        # print(f'Beam setup function: \nAScan Start:{beam.GetAscanStart()}, AScan Length: {beam.GetAscanLength()}')
        AScanStart_current = beam.GetAscanStart()
        AScan_length_current = beam.GetAscanLength()
        Recurrence_current = beam.GetRecurrence()
        AScanStart = beam.SetAscanStart(AScanStart_current)
        AscanLength = beam.SetAscanLength(AScan_length_current)
        Recurrence = beam.SetRecurrence(Recurrence_current)
        


    def create_conventionalUT_beamset_P_and_R(self,pulser_index,receive_index):
        deviceConfiguration = self.device.GetConfiguration()
        ultrasoundConfiguration = deviceConfiguration.GetUltrasoundConfiguration()
        digitizerTechnology = ultrasoundConfiguration.GetDigitizerTechnology(UltrasoundTechnology.Conventional)
        beamSetFactory = digitizerTechnology.GetBeamSetFactory()
        beamSet = beamSetFactory.CreateBeamSetConventional("Conventional")
        pulser = digitizerTechnology.GetConnectorCollection().GetConnector(pulser_index)
        receiver = digitizerTechnology.GetConnectorCollection().GetConnector(receive_index)
        ultrasoundConfiguration.GetFiringBeamSetCollection().Add(beamSet,pulser,receiver)


    def create_pa_beamset(self, connector_index):
        deviceConfiguration = self.device.GetConfiguration()
        ultrasoundConfiguration = deviceConfiguration.GetUltrasoundConfiguration()
        digitizerTechnology = ultrasoundConfiguration.GetDigitizerTechnology(UltrasoundTechnology.PhasedArray)
        """"""
        beamSetFactory = digitizerTechnology.GetBeamSetFactory()
        LawFile_path = ''
        BeamFormationCollection = beamSetFactory.CreateBeamFormationCollectionFromLawFile(LawFile_path)
        beamSet = beamSetFactory.CreateBeamSetPhasedArray("PhasedArray",BeamFormationCollection)
        # ===============================================================================================
        connector = digitizerTechnology.GetConnectorCollection().GetConnector(connector_index)
        ultrasoundConfiguration.GetFiringBeamSetCollection().Add(beamSet, connector)
        """"""

    def switch_to_50(self):
        self.acquisition.Stop()
        self.acquisition.SetRate(50)
        input('PRESS ENTER TO START TEST')
        self.acquisition.Start()

    def switch_to_100(self):
        self.acquisition.Stop()
        self.acquisition.SetRate(10000)
        input('PRESS ENTER TO START TEST')
        self.acquisition.Start()

    def init_acquisition(self):
        self.acquisition = IAcquisition.CreateEx(self.device)
        self.acquisition.SetRate(10)

    def collect_ascan(self):
        try:
            result = self.acquisition.WaitForDataEx()
            if result.status == IAcquisition.WaitForDataResultEx.Status.DataAvailable:
                self.process_ascan(result)  #run it in the main tread
                """run it in another thread"""

        except:
            pass


    def process_ascan(self, result):
        thread_result = result 
        ascan = thread_result.cycleData.GetAscanCollection().GetAscan(0)  #AScan data process
        ascan_ptr = ascan.GetData()
        sample_quantity = ascan.GetSampleQuantity()
        AmplitudeSamplingDataRage_min = ascan.GetAmplitudeSamplingDataRange().GetFloatingMin()
        AmplitudeSamplingDataRage_max = ascan.GetAmplitudeSamplingDataRange().GetFloatingMax()
        # print('Amplitude Sampliding unit:' , ascan.GetAmplitudeSamplingDataRange().GetUnit())  #unit is sample
        AmplitudeSamplingDataRage_resolution = (AmplitudeSamplingDataRage_max-AmplitudeSamplingDataRage_min)/sample_quantity
        AmplitudeDataRange_min = ascan.GetAmplitudeDataRange().GetFloatingMin()
        AmplitudeDataRange_max = ascan.GetAmplitudeDataRange().GetFloatingMax()
        # print("Amplitude Data range Unit: ",ascan.GetAmplitudeDataRange().GetUnit())  #Percent is the unit
        AmplitudeDataRange_resolution = (AmplitudeDataRange_max-AmplitudeDataRange_min) / sample_quantity
        TimeDataRange_min = ascan.GetTimeDataRange().GetFloatingMin()
        TimeDataRange_max = ascan.GetTimeDataRange().GetFloatingMax()
        AscanX_min = TimeDataRange_min * velocity 
        AscanX_max = TimeDataRange_max * velocity
        # print(AscanX_max,AscanX_min, ascan.GetTimeDataRange().GetUnit())  #confirmed to be the nanosecond
        CycleID = thread_result.cycleData.GetCycleId()
        newpnt = ctypes.cast(ascan_ptr.ToInt64(), ctypes.POINTER(ctypes.c_int32))
        
        DataBytes = np.ctypeslib.as_array(newpnt, (sample_quantity,))  # no internal copy   
        # DataBytes =  list(DataBytes)
        """Raw Data"""
        AScan_multiply_reading = DataBytes * np.array([float(AmplitudeSamplingDataRage_resolution)])   #Convert to percent
        X_axis = np.linspace(AscanX_min,AscanX_max,sample_quantity)  #get the Thickness reading for the X-axis
        # try:
        #     print(CycleID,'Sampling Resol', AmplitudeSamplingDataRage_resolution)
        # except:
        print('Cycle ID: ',CycleID, 'Peak Amplitude @ ',np.max(DataBytes),'Rate', self.acquisition.GetRate())
        # """Setup Threshold"""
        # amp_gate_lower_limit = 45
        # Xaxis_lower_limit = 26
        # Xaxis_higher_limit = 120  
        # """Apply gate threshold for both x-axis and amplitude in the ascan"""
        # xaxis_index_processed_arr = np.array(np.where((X_axis > Xaxis_lower_limit) & (X_axis < Xaxis_higher_limit)))[0]
        # amp_index_processed_arr = np.array(np.where(AScan_multiply_reading > amp_gate_lower_limit))
        # overlapping_process_index_arr = np.intersect1d(xaxis_index_processed_arr,amp_index_processed_arr)
        # X_axis_processed = X_axis[overlapping_process_index_arr]
        # amp_axis_processed = AScan_multiply_reading[overlapping_process_index_arr]
        # if (X_axis_processed.size != 0 ) and (amp_axis_processed.size != 0):
        #     the_index = int(((np.where(amp_axis_processed == np.amax(amp_axis_processed)))[0])[0])
        #     # defect_point = [X_axis_processed[the_index],amp_axis_processed[the_index]]
        #     print(f'Cycle ID:{CycleID}, Depth:{X_axis_processed[the_index]}mm, Amplitude{amp_axis_processed[the_index]}%')
        # else:
        #     print(f'Cycle ID:{CycleID}, Sample Quantity: {sample_quantity}')
    


    def on_start(self):
        status = self.acquisition.GetStateEx()
        print(status)
        # if status == self.acquisition.GetStateEx.Stopped:
        if status == 1:
            input('PRESS ENTER TO START TEST')
            self.acquisition.Start()
        # elif status == self.acquisition.GetStateEx.Started:
        elif status == 0:
            print("Test Started")




if __name__ == '__main__':
    ip_address = "192.168.0.1"
    fpx = FPXDevice(ip_address)
    package_name = "FocusPxPackage-1.4"
    fpx.download_firmware_package(package_name)
    fpx.create_beamset(4)
    # fpx.create_conventionalUT_beamset_P_and_R(0,1)
    fpx.init_acquisition()
    fpx.acquisition.ApplyConfiguration()
    input('PRESS ENTER TO START')
    fpx.acquisition.Start()
    # keyboard.add_hotkey('s',lambda:fpx.acquisition.Start())


    keyboard.add_hotkey('s',lambda:fpx.on_start())
    keyboard.add_hotkey('q',lambda:fpx.acquisition.Stop())
    keyboard.add_hotkey('h',lambda:fpx.switch_to_100())
    keyboard.add_hotkey('o',lambda:fpx.switch_to_50())
    """
    Try 1
    """
    while True:
        process_thread = Thread(target=fpx.collect_ascan,daemon=True)
        # process_thread.daemon(Ture)
        process_thread.start()
        process_thread.join()
    # fpx.collect_ascan()


    """
    Try2
    Should comment out Try1 when try to test this 
    """
    # process_thread = Thread(target=fpx.on_start)
    # process_thread.start()
    # process_thread.join
