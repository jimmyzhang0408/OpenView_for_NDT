import clr
import serial
import ctypes
import numpy as np
import keyboard
from threading import Thread
import time
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
clr.FindAssembly("OlympusNDT.Instrumentation.NET.dll")
clr.AddReference('OlympusNDT.Instrumentation.NET')

from OlympusNDT.Instrumentation.NET import Utilities, IDeviceDiscovery, DiscoverResult, IFirmwarePackageScanner
from OlympusNDT.Instrumentation.NET import UltrasoundTechnology, IAcquisition, IAmplitudeSettings


# class process_ascan(Thread):
#     def __init__(self):
def process_ascan(result):
    thread_result = result 
    if thread_result.status == IAcquisition.WaitForDataResultEx.Status.DataAvailable:
        ascan = thread_result.cycleData.GetAscanCollection().GetAscan(0)  #AScan data process
        ascan_ptr = ascan.GetData()

        sample_quantity = ascan.GetSampleQuantity()
        AmplitudeSamplingDataRage_min = ascan.GetAmplitudeSamplingDataRange().GetFloatingMin()
        AmplitudeSamplingDataRage_max = ascan.GetAmplitudeSamplingDataRange().GetFloatingMax()

        AmplitudeDataRange_min = ascan.GetAmplitudeDataRange().GetFloatingMin()
        AmplitudeDataRange_max = ascan.GetAmplitudeDataRange().GetFloatingMax()
        AmplitudeDataRange_resolution = (AmplitudeDataRange_max-AmplitudeDataRange_min) / sample_quantity

        TimeDataRange_min = ascan.GetTimeDataRange().GetFloatingMin()
        TimeDataRange_max = ascan.GetTimeDataRange().GetFloatingMax()

        # print("sample_quantity: %d" % sample_quantity)
        CycleID = thread_result.cycleData.GetCycleId()
        newpnt = ctypes.cast(ascan_ptr.ToInt64(), ctypes.POINTER(ctypes.c_int32))
        # newpnt = ctypes.cast(ascan_ptr.ToInt64(), ctypes.POINTER(ctypes.c_ushort))

        DataBytes = np.ctypeslib.as_array(newpnt, (sample_quantity,))  # no internal copy
        UT_axis_fixed = np.linspace(0,len(DataBytes),sample_quantity)
        # print("sample_quantity: %d" % sample_quantity, CycleID)
        AScan_multiply_reading = DataBytes * np.array([float(AmplitudeDataRange_resolution)])   #Convert to percent
        # ============================================
        # Use scipy to find multiple peaks
        # peak_id, peak_property = find_peaks(DataBytes,height=70) #peak的幅值大于10的都找出来
        # peak_depth = UT_axis_fixed[peak_id]
        max_reading = np.max(AScan_multiply_reading)
        # print(f"Print Cycle ID:{CycleID},peak id:{peak_id},peak depth:{peak_depth}")
        print(f"Print Cycle ID:{CycleID},peak amplitude {max_reading}")
        # ============================================



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
        


        beam = beamSet.GetBeam(0)
        print(f'AScan Start:{beam.GetAscanStart()}, AScan Length: {beam.GetAscanLength()}')
        digitizing_setting = beamSet.GetDigitizingSettings()
        AmplitudeSettings = digitizing_setting.GetAmplitudeSettings()
        AmplitudeSettings.SetAscanDataSize(IAmplitudeSettings.AscanDataSize.TwelveBits)
        print("Bits",AmplitudeSettings.GetAscanDataSize()) 
        AmplitudeSettings.SetAscanRectification(IAmplitudeSettings.RectificationType.Positive)
        print("Rectification",AmplitudeSettings.GetAscanRectification())

        ultrasoundConfiguration.GetFiringBeamSetCollection().Add(beamSet, connector)

    def init_acquisition(self):
        self.acquisition = IAcquisition.CreateEx(self.device)
        print(self.acquisition.GetFiringTrigger())
        # self.acquisition.SetFiringTrigger(IAcquisition.FiringTrigger.Encoder)

        # print(self.acquisition.GetFiringTrigger())


    def switch_rate_10(self):
        self.acquisition.Stop()
        self.acquisition.SetRate(10)
        self.acquisition.ApplyConfiguration()
        self.acquisition.Start()

    def switch_rate_50(self):
        self.acquisition.Stop()
        self.acquisition.SetRate(50)
        self.acquisition.ApplyConfiguration()
        self.acquisition.Start()

    def collect_ascan(self):
        try:
            result = self.acquisition.WaitForDataEx()
            if result.status == IAcquisition.WaitForDataResultEx.Status.DataAvailable:
                process_ascan(result)
        except Exception as e:
            # print("The error raised is: ", e)
            e


    def on_start_clicked(self):
        status = self.acquisition.GetStateEx()
        print(status)
        # if status == IAcquisition.GetStateEx().Stopped:
        if status == 1:

            self.acquisition.Start()
            while True:
                self.collect_ascan()
        elif status == 0:
            pass

    def on_switch_clicked(self):
        self.acquisition.Stop()
        self.acquisition.ApplyConfiguration()
        on_on_start()



def on_on_start():
    # cc=input('Press "S" to start the test\n')
    # while True:
    #     if cc== "S":
    input("Press ENTER TO START TEST")
    fpx.acquisition.Start()
        #     break
        # else:
        #     cc = input("press again\n")
    while True:
        fpx.collect_ascan()


if __name__ == '__main__':
    ip_address = "192.168.0.1"
    fpx = FPXDevice(ip_address)
    package_name = "FocusPxPackage-1.4"
    fpx.download_firmware_package(package_name)
    fpx.create_beamset(2)
    fpx.init_acquisition()

    fpx.acquisition.ApplyConfiguration()
    input("ENTER")
    fpx.acquisition.Start()
    keyboard.add_hotkey('s',lambda:fpx.acquisition.Start())
    keyboard.add_hotkey('q',lambda:fpx.acquisition.Stop())


    while True:
        fpx.collect_ascan()
    

