import tkinter as tk
from tkinter import filedialog
import customtkinter
import os
import re
import json
from utils import resourcePath, generateSweatboxText, Pilot, Airport, Controller
import tkintermapview
from PIL import Image, ImageTk


class App(customtkinter.CTk):
    """Contains methods for the interface and generation of the sweatbox"""

    def __init__(self):
        super().__init__()

        # Modes: "System" (standard), "Dark", "Light"
        customtkinter.set_appearance_mode("Dark")
        # Themes: "blue" (standard), "green", "dark-blue"
        customtkinter.set_default_color_theme("green")

        # configure window
        self.title("Sweatbox Scenario Generator")
        self.geometry(f"{1100}x{650}")

        self.vfrPercentage = tk.IntVar()
        self.invalidRoutePercentage = tk.IntVar()
        self.invalidLevelPercentage = tk.IntVar()
        self.fplanErrorsPercentage = tk.IntVar()

        self.sectorFileLocation = None
        self.outputDirectory = None

        self.manualPilots = []
        self.activeControllers = {}

        self.selectableAirports = {}
        self.loadAirports()
        self.activeAirport = None

        self.loadOptions()

        self.grid_columnconfigure(0, weight=0, minsize=240)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=0, minsize=240)
        self.grid_rowconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(3, weight=0)

        self.airportSelectFrame = customtkinter.CTkFrame(
            self, corner_radius=12)
        self.airportSelectFrame.grid(
            row=0, column=0, rowspan=4, sticky="nsew", padx=5, pady=5)
        self.airportSelectFrame.grid_rowconfigure(3, weight=1)
        self.airportSelectFrame.grid_columnconfigure(0, weight=1)

        airportSelectLabel = customtkinter.CTkLabel(
            self.airportSelectFrame, text="Select Airport", font=customtkinter.CTkFont(size=20, weight="bold"))
        airportSelectLabel.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.placeAirportSelect()

        self.mapFrame = customtkinter.CTkFrame(
            self, corner_radius=12)
        self.mapFrame.grid(row=0, column=1, rowspan=4,
                           columnspan=1, sticky="nsew", padx=5, pady=5)
        self.mapFrame.grid_rowconfigure(0, weight=1)
        self.mapFrame.grid_columnconfigure(0, weight=1)

        self.mapWidget = tkintermapview.TkinterMapView(
            self.mapFrame, corner_radius=12)
        self.mapWidget.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # TODO make Dynamic
        self.mapWidget.set_position(55.9505, -3.3612)
        self.mapWidget.set_zoom(15)

        self.planeIconList = []

        # TODO: Move back to a relevant place?
        self.switchAirport(self.selectableAirports["EGPH"]["airport"])

        self.summaryFrame = customtkinter.CTkFrame(
            self, corner_radius=12)
        self.summaryFrame.grid(row=0, column=2, rowspan=1,
                               sticky="nsew", padx=5, pady=5)
        self.summaryFrame.grid_columnconfigure(0, weight=1)
        self.summaryFrame.grid_rowconfigure(4, weight=1)

        customtkinter.CTkLabel(self.summaryFrame, text="Summary",
                               font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=0, pady=(15, 10))

        self.sliderFrame = customtkinter.CTkFrame(
            self, corner_radius=12)
        self.sliderFrame.grid(row=1, column=2, rowspan=2,
                              sticky="nsew", padx=5, pady=5)
        self.sliderFrame.grid_columnconfigure(0, weight=1)
        self.sliderFrame.grid_rowconfigure(8, weight=1)

        self.placeSliders()

        self.generateFrame = customtkinter.CTkFrame(
            self, corner_radius=12)
        self.generateFrame.grid(row=3, column=2, sticky="nsew", padx=5, pady=5)
        self.generateFrame.grid_columnconfigure(0, weight=1)
        self.generateFrame.grid_rowconfigure(2, weight=1)

        customtkinter.CTkLabel(self.generateFrame, text="Number of Planes",
                               fg_color="transparent").grid(row=0, column=0, padx=20, pady=(10, 5))

        self.numberOfPlanesEntry = customtkinter.CTkEntry(
            self.generateFrame, placeholder_text="20")
        self.numberOfPlanesEntry.grid(row=1, column=0, padx=20, pady=(5, 10))

        self.manualAdd = customtkinter.CTkButton(
            self.generateFrame, text="Add Pilot Manually", command=self.addManualPilot)
        self.manualAdd.grid(row=2, column=0, padx=20, pady=10)

        self.addATC = customtkinter.CTkButton(
            self.generateFrame, text="Add Controllers", command=self.addControllers)
        self.addATC.grid(row=3, column=0, padx=20, pady=10)

        self.generateButton = customtkinter.CTkButton(
            self.generateFrame, text="Generate Sweatbox file", command=self.generate)
        self.generateButton.grid(row=4, column=0, padx=20, pady=10)

    def placeSliders(self) -> None:
        """Place the sliders on the frame
        """

        # VFR Traffic
        self.vfrLabel = customtkinter.CTkLabel(
            self.sliderFrame, text=f"Percentage of VFR Aircraft: 0%", fg_color="transparent", justify="left")
        self.vfrLabel.grid(row=0, column=0, padx=0, pady=10)

        vfrSlider = customtkinter.CTkSlider(
            self.sliderFrame, from_=0, to=100, variable=self.vfrPercentage, command=self.updateVFRLabel)
        vfrSlider.grid(row=1, column=0, padx=5, pady=(0, 20))

        # Invalid Routes
        self.invalidRouteLabel = customtkinter.CTkLabel(
            self.sliderFrame, text=f"Percentage of Invalid Routes: 0%", fg_color="transparent", justify="left")
        self.invalidRouteLabel.grid(row=2, column=0, padx=0, pady=5)

        invalidRouteSlider = customtkinter.CTkSlider(
            self.sliderFrame, from_=0, to=100, variable=self.invalidRoutePercentage, command=self.updateInvalidRouteLabel)
        invalidRouteSlider.grid(row=3, column=0, padx=5, pady=(0, 20))

        # Invalid Levels
        self.invalidLevelLabel = customtkinter.CTkLabel(
            self.sliderFrame, text=f"Percentage of Invalid Levels: 0%", fg_color="transparent", justify="left")
        self.invalidLevelLabel.grid(row=4, column=0, padx=0, pady=5)

        invalidLevelSlider = customtkinter.CTkSlider(
            self.sliderFrame, from_=0, to=100, variable=self.invalidLevelPercentage,
            command=self.updateInvalidLevelLabel)
        invalidLevelSlider.grid(row=5, column=0, padx=5, pady=(0, 20))

        # fPln errors
        self.invalidFplnLabel = customtkinter.CTkLabel(
            self.sliderFrame, text=f"Percentage of Flightplan errors: 0%", fg_color="transparent", justify="left")
        self.invalidFplnLabel.grid(row=6, column=0, padx=0, pady=5)

        invalidFplnSlider = customtkinter.CTkSlider(
            self.sliderFrame, from_=0, to=100, variable=self.fplanErrorsPercentage,
            command=self.updateFplanErrorsLabel)
        invalidFplnSlider.grid(row=7, column=0, padx=5, pady=(0, 20))

    def placeAirportSelect(self) -> None:
        """Place airport select buttons
        """
        airportVar = tk.StringVar(value="Select Airport")
        airportDropdown = customtkinter.CTkOptionMenu(
            self.airportSelectFrame, variable=airportVar, values=list(self.selectableAirports.keys()), command=lambda _: self.switchAirport(self.selectableAirports[airportVar.get()]["airport"]))
        airportDropdown.grid(row=1, column=0, padx=20, pady=10)

    def getSectorFile(self) -> str:
        """Get the location of the sectorfile

        Returns:
            str: Path to sectorfile
        """
        # TODO: Work out what to do / if we need sf
        if not self.sectorFileLocation:
            ukPack = self.selectDirectory("UK controller Pack")
            self.sectorFileLocation = f"{ukPack}/Data/Sector"
            self.writeOptions()
            sector_files = os.listdir(self.sectorFileLocation)
            pattern = re.compile(r"UK_\d{4}_\d{2}\.sct")

            for file in sector_files:
                if pattern.match(file):
                    sectorFilePath = os.path.join(
                        self.sectorFileLocation, file)
                    break

        # TODO: Get the things we need from the SF / Perhaps move to `utils.py`??
        with open(sectorFilePath, "r")as sf:
            ...  # process

    def loadOptions(self) -> None:
        """Load the option file
        """
        if os.path.exists("sweatbox_generator.config"):
            with open("sweatbox_generator.config", "r") as configFile:
                config = configFile.read().split(',')
                if len(config) >= 2:
                    self.sectorFileLocation = config[0]
                    self.outputDirectory = config[1]
        if self.outputDirectory == "()":
            self.outputDirectory = None

    def writeOptions(self) -> None:
        """Update the options file
        """
        with open("sweatbox_generator.config", "w")as configFile:
            configFile.write(f"{self.sectorFileLocation},")
            configFile.write(f"{self.outputDirectory},")

    def selectDirectory(self, dir: str) -> str:
        """Get the user to select the location of a directory

        Args:
            dir (str): Name of directory to find

        Returns:
            str: Path to directory
        """
        return filedialog.askdirectory(title=f"Select {dir}")

    def getControllers(self) -> list[Controller]:
        with open(resourcePath("rsc/controllers.json"))as f:
            data = json.load(f)
        controllers = []
        for airport in self.activeControllers:
            for pos in self.activeControllers[airport]:
                freq = data[airport][pos]
                controllers.append(Controller(
                    airport, "GND", f"{airport}_{pos}", freq))

        return controllers

    def generate(self) -> None:
        """Generate the sweatbox file, and destroy the window
        """
        controllers = self.getControllers()
        if not self.numberOfPlanesEntry.get():
            numberOfPlanes = 20
        else:
            numberOfPlanes = self.numberOfPlanesEntry.get()

        print(f"SYSTEM: GENERATING SWEATBOX FILE")
        print(f"SYSTEM: {numberOfPlanes=}")
        print(f"SYSTEM: {self.vfrPercentage.get()=}%")
        print(f"SYSTEM: {self.invalidRoutePercentage.get()=}%")
        print(f"SYSTEM: {self.invalidLevelPercentage.get()=}%")
        print(f"SYSTEM: {self.fplanErrorsPercentage.get()=}%")

        self.sweatboxContents = generateSweatboxText(self.activeAirport, self.selectableAirports[self.activeAirport.icao]["approachData"], int(self.vfrPercentage.get()), int(self.invalidRoutePercentage.get()),
                                                     int(self.invalidLevelPercentage.get()), int(self.fplanErrorsPercentage.get()), controllers, int(numberOfPlanes), self.manualPilots)

        print(f"SYSTEM: GENERATED SWEATBOX FILE")

        if self.outputDirectory:
            fileName = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("Text files", "*.txt")], initialdir=self.outputDirectory)
        else:
            fileName = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("Text files", "*.txt")])

        if not self.outputDirectory or os.path.dirname(fileName) != self.outputDirectory:
            self.outputDirectory = os.path.dirname(fileName)
            self.writeOptions()

        if not fileName:
            print("ERROR: COULD NOT OUTPUT FILE")
            return
        with open(fileName, "w")as outFile:
            outFile.write(self.sweatboxContents)

        print(f"SYSTEM: FILE WRITTEN TO {fileName}")
        print(f"SYSTEM: BYE")
        self.destroy()

    def updateVFRLabel(self, value) -> None:
        self.vfrLabel.configure(
            text=f"Percentage of VFR Aircraft: {int(value)}%")

    def updateInvalidRouteLabel(self, value) -> None:
        self.invalidRouteLabel.configure(
            text=f"Percentage of Invalid Routes: {int(value)}%")

    def updateInvalidLevelLabel(self, value) -> None:
        self.invalidLevelLabel.configure(
            text=f"Percentage of Invalid Level: {int(value)}%")

    def updateFplanErrorsLabel(self, value) -> None:
        self.invalidFplnLabel.configure(
            text=f"Percentage of Flightplan Errors: {int(value)}%")

    def switchAirport(self, airport: Airport) -> None:
        """Switch the active airport and center the map

        Args:
            airport (Airport): New airport
        """
        self.activeAirport = airport
        print(f"SYSTEM: ACTIVE AIRPORT {airport.icao}")
        # self.mapWidget.set_address("colosseo, rome, italy") TODO - Center map

    def loadAirports(self) -> None:
        """Load airport data from file
        """
        # Import initial airport data
        with open(resourcePath("rsc/airportConfig.json")) as configData:
            airportConfigs = json.load(configData)

        for airport in airportConfigs:
            elevation = airportConfigs[airport]["elevation"]
            runway = airportConfigs[airport]["runway"]
            position = airportConfigs[airport]["position"]
            appData = airportConfigs[airport]["approachData"]
            appDataStr = "\n".join(
                [f"{value}" for _, value in appData.items()])

            self.selectableAirports[airport] = {}
            self.selectableAirports[airport]["airport"] = Airport(
                airport, elevation, runway, position)
            self.selectableAirports[airport]["approachData"] = appDataStr

    def addManualPilot(self) -> None:
        """Open a new window to add a manual pilot
        """
        newWindow = customtkinter.CTkToplevel(self)
        newWindow.title("Add Manual Pilot")
        newWindow.geometry("350x500")

        def save_pilot() -> None:
            callsign = callsignEntry.get()
            lat = latEntry.get()
            long = longEntry.get()
            alt = self.currentAirport.altitude
            hdg = int(hdgEntry.get())
            dep = self.currentAirport.icao
            sq = f"{len(self.manualPilots):04}"
            rules = str(rulesVar)
            acType = typeEntry.get()
            cruiseLvl = cruiseLvlEntry.get()
            dest = destEntry.get()
            rmk = rmkVar.get()
            route = routeEntry.get()

            pilot = Pilot(callsign, lat, long, alt, hdg, dep, sq,
                          rules, acType, cruiseLvl, dest, rmk, route, route)
            self.manualPilots.append(pilot)
            # newWindow.destroy()

        customtkinter.CTkLabel(newWindow, text="Enter Pilot Details", font=customtkinter.CTkFont(
            size=15, weight="bold")).grid(row=0, column=0, columnspan=2, pady=10)

        customtkinter.CTkLabel(newWindow, text="Callsign").grid(
            row=1, column=0, pady=5, sticky="e")
        callsignEntry = customtkinter.CTkEntry(newWindow)
        callsignEntry.grid(row=1, column=1, pady=5, padx=5)

        customtkinter.CTkLabel(newWindow, text="Latitude").grid(
            row=2, column=0, pady=5, sticky="e")
        latEntry = customtkinter.CTkEntry(newWindow)
        latEntry.grid(row=2, column=1, pady=5, padx=5)

        customtkinter.CTkLabel(newWindow, text="Longitude").grid(
            row=3, column=0, pady=5, sticky="e")
        longEntry = customtkinter.CTkEntry(newWindow)
        longEntry.grid(row=3, column=1, pady=5, padx=5)

        customtkinter.CTkLabel(newWindow, text="Heading").grid(
            row=4, column=0, pady=5, sticky="e")
        hdgEntry = customtkinter.CTkEntry(newWindow)
        hdgEntry.grid(row=4, column=1, pady=5, padx=5)

        customtkinter.CTkLabel(newWindow, text="Flight Rules").grid(
            row=5, column=0, pady=5, sticky="e")
        rulesVar = tk.StringVar(value="I")
        ifrRadio = customtkinter.CTkRadioButton(
            newWindow, text="IFR", variable=rulesVar, value="I")
        ifrRadio.grid(row=5, column=1, padx=(10, 5), pady=5, sticky="w")
        vfrRadio = customtkinter.CTkRadioButton(
            newWindow, text="VFR", variable=rulesVar, value="V")
        vfrRadio.grid(row=5, column=2, padx=(5, 10), pady=5, sticky="w")

        customtkinter.CTkLabel(newWindow, text="Aircraft Type").grid(
            row=6, column=0, pady=5, sticky="e")
        typeEntry = customtkinter.CTkEntry(newWindow)
        typeEntry.grid(row=6, column=1, pady=5, padx=5)

        customtkinter.CTkLabel(
            newWindow, text="Cruise Level (in ft)").grid(row=7, column=0, pady=5, sticky="e")
        cruiseLvlEntry = customtkinter.CTkEntry(newWindow)
        cruiseLvlEntry.grid(row=7, column=1, pady=5, padx=5)

        customtkinter.CTkLabel(
            newWindow, text="Destination (ICAO)").grid(row=8, column=0, pady=5, sticky="e")
        destEntry = customtkinter.CTkEntry(newWindow)
        destEntry.grid(row=8, column=1, pady=5, padx=5)

        customtkinter.CTkLabel(newWindow, text="Voice Rules").grid(
            row=9, column=0, pady=5, sticky="e")
        rmkVar = tk.StringVar(value="none")
        vRadio = customtkinter.CTkRadioButton(
            newWindow, text="V", variable=rmkVar, value="V")
        vRadio.grid(row=9, column=1, padx=(10, 5), pady=5, sticky="w")
        rRadio = customtkinter.CTkRadioButton(
            newWindow, text="R", variable=rmkVar, value="R")
        rRadio.grid(row=9, column=2, padx=(5, 10), pady=5, sticky="w")
        tRadio = customtkinter.CTkRadioButton(
            newWindow, text="T", variable=rmkVar, value="T")
        tRadio.grid(row=9, column=3, padx=(5, 10), pady=5, sticky="w")
        noneRadio = customtkinter.CTkRadioButton(
            newWindow, text="None", variable=rmkVar, value="none")
        noneRadio.grid(row=9, column=4, padx=(5, 10), pady=5, sticky="w")

        customtkinter.CTkLabel(newWindow, text="Route").grid(
            row=10, column=0, pady=5, sticky="e")
        routeEntry = customtkinter.CTkEntry(newWindow)
        routeEntry.grid(row=10, column=1, pady=5, padx=5)

        save_button = customtkinter.CTkButton(
            newWindow, text="Add pilot", command=save_pilot)
        save_button.grid(row=11, column=0, columnspan=2, pady=20)

    def addControllers(self) -> None:
        controllerWindow = customtkinter.CTkToplevel(self)
        controllerWindow.title("Add Controllers")
        controllerWindow.geometry("350x500")
        controllerWindow.grid_columnconfigure(0, weight=1)

        def saveControllers() -> None:
            controllerWindow.destroy()

        with open(resourcePath("rsc/controllers.json"))as f:
            controllers = json.load(f)

        save_button = customtkinter.CTkButton(
            controllerWindow, text="Add Selected Controllers", command=saveControllers)
        save_button.grid(row=0, column=0, pady=20)

        controllerVar = tk.StringVar(value="Select Controller")
        controllerDropdown = customtkinter.CTkOptionMenu(
            controllerWindow, variable=controllerVar, values=list(controllers.keys()), command=lambda _: updateControllerInfo())
        controllerDropdown.grid(
            row=1, column=0, pady=10, padx=10)

        def saveCheckboxState(controller, pos, var):
            self.activeControllers[controller][pos] = var.get()

        def updateControllerInfo():
            selected_controller = controllerVar.get()
            if selected_controller in controllers:
                for widget in controllerWindow.grid_slaves():
                    if int(widget.grid_info()["row"]) > 1:
                        widget.grid_forget()

                info = controllers[selected_controller]
                if selected_controller not in self.activeControllers:
                    self.activeControllers[selected_controller] = {}
                for pos, freq in info.items():
                    var = tk.BooleanVar(
                        value=self.activeControllers[selected_controller].get(pos, False))
                    checkbox = customtkinter.CTkCheckBox(
                        controllerWindow, text=f"{selected_controller}_{pos} ({freq})", variable=var)
                    checkbox.grid(row=2 + list(info.keys()).index(pos),
                                  column=0, pady=5, padx=10)
                    var.trace_add("write", lambda *args, pos=pos,
                                  var=var: saveCheckboxState(selected_controller, pos, var))

    def placeAircraftIcon(self, airportICAO: str, standNumber: str) -> None:
        with open(resourcePath("rsc/stands.json"))as f:
            standData = json.load(f)
        lat, long, heading = standData[airportICAO][standNumber].split(",")
        image = Image.open(resourcePath("icons8-plane-50.png"))
        # TODO: make dynamic scaling
        resized_image = image.resize((20, 20))
        rotated_image = resized_image.rotate(
            90 - int(heading))  # Rotate to the north, then thank Tkinter
        planeIcon = ImageTk.PhotoImage(rotated_image)
        self.planeIconList.append(planeIcon)
        self.mapWidget.set_marker(
            float(lat), float(long), icon=planeIcon)


if __name__ == "__main__":
    app = App()
    app.mainloop()
