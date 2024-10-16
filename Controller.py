import sys
sys.path.append(r"C:\Program Files (x86)\CST STUDIO SUITE 2023\AMD64\python_cst_libraries")
import cst
import cst.results as cstr
import cst.interface as csti
import os
import numpy as np
import matplotlib.pyplot as plt
import csv

class CSTInterface:
    def __init__(self, fname):
        self.full_path = os.getcwd() + f"\{fname}"
        self.opencst()

    def opencst(self):
        print("CST opening...")
        allpids = csti.running_design_environments()
        open = False
        for pid in allpids:
            self.de = csti.DesignEnvironment.connect(pid)
            self.de.set_quiet_mode(True) # suppress message box
            print(f"Opening {self.full_path}...")
            self.prj = self.de.open_project(self.full_path)
            open = True
            print(f"{self.full_path} open")
            break
        if not open:
            print("File path not found in current design environment...")
            print("Opening new design environment...")
            self.de = csti.DesignEnvironment.new()
            self.de.set_quiet_mode(True) # suppress message box
            self.prj = self.de.open_project(self.full_path)
            open = True
            print(f"{self.full_path} open")
        # I wish to create project if not created, but I don't know how to.
        # Therefore, the user need to create *.cst file in advance

    def read(self, result_item):
        results = cstr.ProjectFile(self.full_path, True) #bool: allow interactive
        try:
            res = results.get_3d().get_result_item(result_item)
            res = res.get_data()
        except:
            print("No result item. Available result items listed below")
            print(results.get_3d().get_tree_items())
            res = None
        return res

    def save(self):
        self.prj.modeler.full_history_rebuild() 
        #update history, might discard changes if not added to history list
        self.prj.save()

    def close(self):
        self.de.close()

    def excute_vba(self,  command):
        command = "\n".join(command)
        vba = self.prj.schematic
        res = vba.execute_vba_code(command)
        return res

    def create_para(self,  para_name, para_value): #create or change are the same
        command = ['Sub Main', 'StoreDoubleParameter("%s", "%.4f")' % (para_name, para_value),
                'RebuildOnParametricChange(False, True)', 'End Sub']
        res = self.excute_vba (command)
        return command
    
    def create_shape(self, index, xmin, xmax, ymin, ymax, hc): #create or change are the same
        command = ['With Brick', '.Reset ', f'.Name "solid{index}" ', 
                   '.Component "component2" ', f'.Material "material{index}" ', 
                   f'.Xrange "{xmin}", "{xmax}" ', f'.Yrange "{ymin}", "{ymax}" ', 
                   f'.Zrange "0", "{hc}" ', '.Create', 'End With']
        return command
        # command = "\n".join(command)
        # self.prj.modeler.add_to_history(f"solid{index}",command)
    
    def create_cond_material(self, index, sigma, type="Lossy metal"): #create or change are the same
        command = ['With Material', '.Reset ', f'.Name "material{index}"', 
                #    '.Folder ""', '.Rho "8930"', '.ThermalType "Normal"', 
                #    '.ThermalConductivity "401"', '.SpecificHeat "390", "J/K/kg"', 
                #    '.DynamicViscosity "0"', '.UseEmissivity "True"', '.Emissivity "0"', 
                #    '.MetabolicRate "0.0"', '.VoxelConvection "0.0"', 
                #    '.BloodFlow "0"', '.MechanicsType "Isotropic"', 
                #    '.YoungsModulus "120"', '.PoissonsRatio "0.33"', 
                #    '.ThermalExpansionRate "17"', '.IntrinsicCarrierDensity "0"', 
                   '.FrqType "all"', f'.Type "{type}"', 
                   '.MaterialUnit "Frequency", "GHz"', '.MaterialUnit "Geometry", "mm"', 
                   '.MaterialUnit "Time", "ns"', '.MaterialUnit "Temperature", "Celsius"', 
                   '.Mu "1"', f'.Sigma "{sigma}"', 
                   '.LossyMetalSIRoughness "0.0"', '.ReferenceCoordSystem "Global"', 
                   '.CoordSystemType "Cartesian"', '.NLAnisotropy "False"', 
                   '.NLAStackingFactor "1"', '.NLADirectionX "1"', '.NLADirectionY "0"', 
                   '.NLADirectionZ "0"', '.Colour "0", "1", "1" ', '.Wireframe "False" ', 
                   '.Reflection "False" ', '.Allowoutline "True" ', 
                   '.Transparentoutline "False" ', '.Transparency "0" ', 
                   '.Create', 'End With']
        return command
        # command = "\n".join(command)
        # self.prj.modeler.add_to_history(f"material{index}",command)

    def start_simulate(self):
        try: # problems occur with extreme conditions
            # one actually should not do try-except otherwise severe bug may NOT be detected
            model = self.prj.modeler
            model.run_solver()
        except Exception as e: pass
    
    def set_plane_wave(self):  # doesn't update history, disappear after save but remain after simulation
        command = ['Sub Main', 'With PlaneWave', '.Reset ', 
                   '.Normal "0", "0", "-1" ', '.EVector "1", "0", "0" ', 
                   '.Polarization "Linear" ', '.ReferenceFrequency "2" ', 
                   '.PhaseDifference "-90.0" ', '.CircularDirection "Left" ', 
                   '.AxialRatio "0.0" ', '.SetUserDecouplingPlane "False" ', 
                   '.Store', 'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def set_excitation(self, filePath): # doesn't update history, disappear after save but remain after simulation. 
        # set .UseCopyOnly to false otherwise CST read cache
        command = ['Sub Main', 'With TimeSignal ', '.Reset ', 
                   '.Name "signal1" ', '.SignalType "Import" ', 
                   '.ProblemType "High Frequency" ', 
                   f'.FileName "{filePath}" ', 
                   '.Id "1"', '.UseCopyOnly "false" ', '.Periodic "False" ', 
                   '.Create ', 'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def delete_plane_wave(self):
        command = ['Sub Main', 'PlaneWave.Delete', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def delete_signal1(self):
        command = ['Sub Main', 'With TimeSignal', 
     '.Delete "signal1", "High Frequency" ', 'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def set_port(self):
        command = ['Sub Main', 'Pick.PickEdgeFromId "component1:feed", "1", "1"', 
                   'Pick.PickEdgeFromId "component1:coaxouter", "1", "1"', 
                   'With DiscreteFacePort ', '.Reset ', '.PortNumber "1" ', 
                   '.Type "SParameter"', '.Label ""', '.Folder ""', '.Impedance "50.0"', 
                   '.VoltageAmplitude "1.0"', '.CurrentAmplitude "1.0"', '.Monitor "True"', 
                   '.CenterEdge "True"', '.SetP1 "True", "5.7", "-0.5", "-6.635"', 
                   '.SetP2 "True", "6.6", "-0.5", "-6.635"', '.LocalCoordinates "False"', 
                   '.InvertDirection "False"', '.UseProjection "False"', 
                   '.ReverseProjection "False"', '.FaceType "Linear"', '.Create ', 
                   'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def delete_port(self):
        command = ['Sub Main', 'Port.Delete "1"', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def export_E_field(self, outputPath, resultPath, step):
        command = ['Sub Main',
        'SelectTreeItem  ("%s")' % resultPath, 
        'With ASCIIExport', '.Reset',
        f'.FileName ("{outputPath}")',
        '.SetSampleRange(0, 35)',
        '.Mode ("FixedWidth")', '.Step (%s)' % step,
        '.Execute', 'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def export_power(self, outputPath, resultPath):
        command = ['Sub Main',
        'SelectTreeItem  ("%s")' % resultPath, 
        'With ASCIIExport', '.Reset',
        f'.FileName ("{outputPath}")',
        '.SetSampleRange(0, 35)',
        '.StepX (4)', '.StepY (4)',
        '.Execute', 'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def delete_results(self):
        command = ['Sub Main',
        'DeleteResults', 'End Sub']
        res = self.excute_vba(command)
        return res
 

class Controller(CSTInterface):
    def __init__(self, fname):
        super().__init__(fname)

    # initialize ground, substrate, feed, and port
    def set_base(self, Lg=104, Wg=104, hc=0.035, hs=1.6, feedx=5, feedy=-0.5):
        print("Setting base...")
        # Create ground, substrate, feed, and port
        ground = ['Component.New "component1"', 'Component.New "component2"',
                   'With Brick', '.Reset ', 
                   '.Name "ground" ', '.Component "component1" ', 
                   '.Material "Copper (annealed)" ', f'.Xrange "{-Lg/2}", "{Lg/2}" ', 
                   f'.Yrange "{-Wg/2}", "{Wg/2}" ', f'.Zrange "{-hc-hs}", "{-hs}" ', '.Create', 'End With']
        substrate = ['With Material', '.Reset', '.Name "FR-4 (lossy)"', 
                   '.Folder ""', '.FrqType "all"', '.Type "Normal"', 
                   '.SetMaterialUnit "GHz", "mm"', '.Epsilon "4.3"', '.Mu "1.0"', 
                   '.Kappa "0.0"', '.TanD "0.025"', '.TanDFreq "10.0"', 
                   '.TanDGiven "True"', '.TanDModel "ConstTanD"', '.KappaM "0.0"', 
                   '.TanDM "0.0"', '.TanDMFreq "0.0"', '.TanDMGiven "False"', 
                   '.TanDMModel "ConstKappa"', '.DispModelEps "None"', 
                   '.DispModelMu "None"', '.DispersiveFittingSchemeEps "General 1st"', 
                   '.DispersiveFittingSchemeMu "General 1st"', 
                   '.UseGeneralDispersionEps "False"', '.UseGeneralDispersionMu "False"', 
                   '.Rho "0.0"', '.ThermalType "Normal"', '.ThermalConductivity "0.3"', 
                   '.SetActiveMaterial "all"', '.Colour "0.94", "0.82", "0.76"', 
                   '.Wireframe "False"', '.Transparency "0"', '.Create', 'End With',
                   'With Brick', '.Reset ', '.Name "substrate" ', 
                   '.Component "component1" ', '.Material "FR-4 (lossy)" ', 
                   f'.Xrange "{-Lg/2}", "{Lg/2}" ', f'.Yrange "{-Wg/2}", "{Wg/2}" ', 
                   f'.Zrange "{-hs}", "0" ', '.Create', 'End With ']
        ground_sub = ['With Cylinder ', '.Reset ', '.Name "sub" ', '.Component "component1" ', 
                   '.Material "Copper (annealed)" ', f'.OuterRadius "{hs}" ', 
                   '.InnerRadius "0.0" ', '.Axis "z" ', f'.Zrange "{-hc-hs}", "{-hs}" ', 
                   f'.Xcenter "{feedx}" ', f'.Ycenter "{feedy}" ', '.Segments "0" ', '.Create ', 
                   'End With', 'Solid.Subtract "component1:ground", "component1:sub"']
        substrate_sub = ['With Cylinder ', '.Reset ', '.Name "feedsub" ', 
                   '.Component "component1" ', '.Material "FR-4 (lossy)" ', 
                   f'.OuterRadius "{hs/2-0.1}" ', '.InnerRadius "0.0" ', '.Axis "z" ', 
                   f'.Zrange "{-hs}", "0" ', f'.Xcenter "{feedx}" ', f'.Ycenter "{feedy}" ', 
                   '.Segments "0" ', '.Create ', 'End With', 
                   'Solid.Subtract "component1:substrate", "component1:feedsub"'] 
        feed = ['With Cylinder ', '.Reset ', '.Name "feed" ', '.Component "component1" ', 
                   '.Material "PEC" ', f'.OuterRadius "{hs/2-0.1}" ', '.InnerRadius "0.0" ', 
                   '.Axis "z" ', f'.Zrange "{-5-hc-hs}", "{hc}" ', f'.Xcenter "{feedx}" ', 
                   f'.Ycenter "{feedy}" ', '.Segments "0" ', '.Create ', 'End With']
        coax = ['With Cylinder ', '.Reset ', '.Name "coax" ', '.Component "component1" ', 
                   '.Material "Vacuum" ', f'.OuterRadius "{hs-0.01}" ', f'.InnerRadius "{hs/2-0.1}" ', 
                   '.Axis "z" ', f'.Zrange "{-5-hc-hs}", "{-hc-hs}" ', f'.Xcenter "{feedx}" ', 
                   f'.Ycenter "{feedy}" ', '.Segments "0" ', '.Create ', 'End With', 
                   'With Cylinder ', '.Reset ', '.Name "coaxouter" ', 
                   '.Component "component1" ', '.Material "PEC" ', f'.OuterRadius "{hs}" ', 
                   f'.InnerRadius "{hs-0.01}" ', '.Axis "z" ', f'.Zrange "{-5-hc-hs}", "{-hc-hs}" ', 
                   f'.Xcenter "{feedx}" ', f'.Ycenter "{feedy}" ', '.Segments "0" ', '.Create ', 
                   'End With']
        command = ground + substrate + ground_sub + substrate_sub + feed + coax
        command = "\n".join(command)
        self.prj.modeler.add_to_history("initialize",command)
        self.save()
        print("Base set")
    
    def set_monitor(self, Ld, d, hc=0.035, hs=1.6, feedx=5, feedy=-0.5):
        print("Setting monitor...")
        margin = (Ld - d)/2
        # Set monitor to read E field on domain
        EonPatch = ['With Monitor ', '.Reset ', '.Name "E_field_on_patch" ', 
                   '.Dimension "Volume" ', '.Domain "Time" ', '.FieldType "Efield" ', 
                   '.Tstart "0" ', '.Tstep "0.1" ', '.Tend "3.5" ', '.UseTend "True" ', 
                   '.UseSubvolume "True" ', '.Coordinates "Free" ', 
                   f'.SetSubvolume "0", "0", "0", "0", "{-5-hc-hs}", "{hc}" ', 
                   f'.SetSubvolumeOffset "{margin}", "{margin}", "{margin}", "{margin}", "{margin}", "{margin}" ', 
                   '.SetSubvolumeInflateWithOffset "True" ', '.PlaneNormal "z" ', 
                   f'.PlanePosition "{hc}" ', '.Create ', 'End With']
        # Set monitor to read power at feed
        PonFeed = ['With Monitor ', 
                   '.Reset ', '.Name "power_on_feed" ', '.Dimension "Volume" ', 
                   '.Domain "Time" ', '.FieldType "Powerflow" ', 
                   '.Tstart "0" ', '.Tstep "0.1" ', '.Tend "3.5" ', 
                   '.UseTend "True" ', '.UseSubvolume "True" ', '.Coordinates "Free" ', 
                   f'.SetSubvolume "{feedx-1}", "{feedx+1}", "{feedy-1}", "{feedy+1}", "{-5-hc-hs}", "{hc}" ', 
                   '.SetSubvolumeOffset "0.0", "0.0", "0.0", "0.0", "0.0", "0.0" ', 
                   '.SetSubvolumeInflateWithOffset "True" ', '.PlaneNormal "z" ', 
                   '.PlanePosition "0.035" ', '.Create ', 'End With']
        command = EonPatch + PonFeed
        command = "\n".join(command)
        self.prj.modeler.add_to_history("set monitor",command)
        self.save()
        print("Monitor set")

    def set_domain(self, Ld, Wd, d, hc=0.035): 
        print("Setting domain...")
        # Initialize domain with uniform conductivity
        nx, ny = (int(Ld//d), int(Wd//d))
        cond = np.zeros(nx*ny)
        print(f"{nx*ny} pixels in total...")
        # Define materials first
        self.update_distribution(cond)
        command = []
        # Define shape and index based on materials
        for index, sigma in enumerate(cond): 
            midpoint = (Ld/2, Wd/2)
            xi = index%nx
            yi = index//nx
            xmin = xi*d-midpoint[0]
            xmax = xmin+d
            ymin = yi*d-midpoint[1]
            ymax = ymin+d
            command += self.create_shape(index, xmin, xmax, ymin, ymax, hc)
        command = "\n".join(command)
        self.prj.modeler.add_to_history("domain",command)
        self.save()
        print("Domain set")

    def update_distribution(self, cond):
        print("Conductivity distribution updating...")
        command_material = []
        for index, sigma in enumerate(cond):
            if sigma < 9000: command_material += self.create_cond_material(index, sigma, "Normal")
            else: command_material += self.create_cond_material(index, sigma)
        command_material = "\n".join(command_material)
        self.prj.modeler.add_to_history("material update",command_material)
        print("Conductivity distribution updated")

    def feed_excitation(self, feedPath, step):
        print("Start feed exciation")
        # Import feed file
        print("fe: importing feed file")
        feedPath = os.getcwd() + "\\" + feedPath
        self.set_excitation(feedPath)
        # Start simulation with feed
        print("fe: simulating")
        self.set_port()
        self.start_simulate()
        # Export E field on patch to txt
        E_Path = "txtf\E_excited.txt"
        outputPath = os.getcwd() + "\\" + E_Path
        self.export_E_field(outputPath, "2D/3D Results\\E-Field\\E_field_on_patch [1]", step)
        print(f"fe: electric field exported as {outputPath}")
        # Record s11 to s11.csv
        s11 = self.read('1D Results\\S-Parameters\\S1,1')
        with open('txtf\\s11.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for line in s11: # [[freq, s11, 50+j],...]
                line = np.abs(line) # change s11 from complex to absolute
                line[1] = 20*np.log10(line[1]) # convert to dB
                writer.writerow(line[:-1])
            writer.writerow([]) # space line for seperation from next call
        # Must delete before return, otherwise CST will save and raise popup window in next iteration
        self.delete_results() # otherwise CST may raise popup window
        self.delete_signal1() # otherwise CST may raise popup window
        self.delete_port() # otherwise CST may raise popup window
        print(f"Return E_Path")
        return E_Path

    def plane_wave_excitation(self, step, excitePath=None):
        print("Start plane wave excitation")
        # Import excitation file
        if excitePath: 
            print("pw: importing specified excitation file")
            excitePath = os.getcwd() + "\\" + excitePath
            self.set_excitation(excitePath)
        # Start simulation with plane wave
        print("pw: simulating")
        self.set_plane_wave()
        self.start_simulate()
        # Export E field on patch to txt
        E_Path = "txtf\E_received.txt"
        outputPath = os.getcwd() + "\\" + E_Path
        self.export_E_field(outputPath, "2D/3D Results\\E-Field\\E_field_on_patch [pw]", step)
        print(f"pw: electric field exported as {outputPath}")
        # Legacy?-----------------------------------
        # # Return power on feed, must set Result Template on CST by hand in advance (IDK how to do it by code)
        # print("pw: return power on feed")
        # power = self.read("Tables\\1D Results\\power_on_feed (pw)_Abs_0D")
        # self.save() ------------------------------
        # Export Power Flow to txt
        powerPath = "txtf\power.txt"
        outputPath = os.getcwd() + "\\" + powerPath
        self.export_power(outputPath, "2D/3D Results\\Power Flow\\power_on_feed [pw]")
        print(f"pw: power flow exported as {outputPath}")
        # Must delete before return, otherwise CST will save and raise popup window in next iteration
        self.delete_results() # otherwise CST may raise popup window
        self.delete_plane_wave() # otherwise CST may raise popup window
        print(f"Return E_Path and powerPath")
        return E_Path, powerPath
    



