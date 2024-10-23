"""Classes to manage KiCad board items

Author:
    (C) Marvin Mager - @mvnmgrx - 2022

License identifier:
    GPL-3.0

Major changes:
    20.02.2022 - created

Documentation taken from:
    https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List

from kiutils.items.common import Position
from kiutils.utils.strings import dequote
from kiutils.utils import sexpr

@dataclass
class GeneralSettings():
    """The ``general`` token define general information about the board

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/#_general_section
    """

    thickness: float = 1.6
    """The ``thickness`` token attribute defines the overall board thickness"""
    legacyTeardrops: str = 'no'
    """The ``legacyTeardrops`` token attribute defines if legacy teardrops are used """

    @classmethod
    def from_sexpr(cls, exp: list) -> GeneralSettings:
        """Convert the given S-Expresstion into a GeneralSettings object

        Args:
            - exp (list): Part of parsed S-Expression ``(general ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not general

        Returns:
            - GeneralSettings: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'general':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'thickness': object.thickness = item[1]
            if item[0] == 'legacy_teardrops': object.legacyTeardrops = item[1]
        return object

    def to_sexpr(self, indent=2, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        expression =  f'{indents}(general\n'
        expression += f'{indents}  (thickness {self.thickness}) (legacy_teardrops {self.legacyTeardrops})\n'
        expression += f'{indents}){endline}'
        return expression


@dataclass
class LayerToken():
    """Intermediate type used for the ``layers`` token in a board

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/#_layers_section
    """

    ordinal: int = 0
    """The layer ``ordinal`` is an integer used to associate the layer stack ordering. This is mostly
    to ensure correct mapping when the number of layers is increased in the future"""

    name: str = "F.Cu"
    """The ``name`` is the layer name defined for internal board use"""

    type: str = "signal"
    """The layer ``type`` defines the type of layer and can be defined as ``jumper``, ``mixed``, ``power``,
    ``signal``, or ``user``."""

    userName: Optional[str] = None
    """The optional ``userName`` attribute defines the custom user name"""

    @classmethod
    def from_sexpr(cls, exp: list) -> LayerToken:
        """Convert the given S-Expresstion into a LayerToken object

        Args:
            - exp (list): Part of parsed S-Expression ``(<nr> "<name>" <type>)``

        Raises:
            - Exception: When given parameter's type is not a list or the length of the list is not 3 - 4
            - Exception: When the first item of the list is not kicad_pcb

        Returns:
            - LayerToken: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list) or len(exp) < 3 or len(exp) > 4:
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.ordinal = exp[0]
        object.name = exp[1]
        object.type = exp[2]
        if len(exp) == 4:
            object.userName = exp[3]
        return object

    def to_sexpr(self, indent=4, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 4.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        username = f' "{dequote(self.userName)}"' if self.userName is not None else ''

        return f'{indents}({self.ordinal} "{dequote(self.name)}" {self.type}{username}){endline}'


@dataclass
class StackupSubLayer():
    """The ``StackupSubLayer`` token defines a sublayer used when stacking dielectrics in a PCB"""

    thickness: float = 0.1
    """The ``thickness`` token defines the thickness of the sublayer. Defaults to 0.1"""

    material: Optional[str] = None
    """The optional ``material`` token defines a string that describes the sublayer material"""

    epsilonR: Optional[float] = None
    """The optional ``epsilonR`` token defines the dielectric constant of the sublayer material"""

    lossTangent: Optional[float] = None
    """The optional layer ``lossTangent`` token defines the dielectric loss tangent of the sublayer"""

    @classmethod
    def from_sexpr(cls, exp: list) -> StackupSubLayer:
        """This class cannot be derived from an S-Expression as the format currently used in KiCad
        board files does not match the usual convention. Assign member values manually when using
        this object.

        Raises:
            - NotImplementedError"""
        raise NotImplementedError("This class cannot be derived from an S-Expression!")

    def to_sexpr(self, indent=0, newline=False) -> str:
        """Generate the S-Expression representing this object. The representation differs from the
        normal form of an S-Expression as this uses no opening and closing parenthesis.

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to False.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        mat = f' (material "{dequote(self.material)}")' if self.material is not None else ''
        er = f' (epsilon_r {self.epsilonR})' if self.epsilonR is not None else ''
        lt = f' (loss_tangent {self.lossTangent})' if self.lossTangent is not None else ''

        return f'{indents}addsublayer (thickness {self.thickness}){mat}{er}{lt}{endline}'


@dataclass
class StackupLayer():
    """The ``layer`` token defines the stack up setting of a single layer in the board stack up
    settings.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/#_stack_up_settings
    """

    name: str = ""
    """The ``name`` attribute is either one of the canonical copper or technical layer names
    or ``dielectric ID`` if it is dielectric layer"""

    # Not found in example project ...
    #number: int = 0
    """The ``number`` attribute defines the stack order of the layer"""

    type: str = ""
    """The ``type`` token defines a string that describes the layer"""

    color: Optional[str] = None
    """The optional ``color`` token defines a string that describes the layer color. This is
    only used on solder mask and silkscreen layers"""

    thickness: Optional[float] = None
    """The optional ``thickness`` token defines the thickness of the layer where appropriate"""

    material: Optional[str] = None
    """The optional ``material`` token defines a string that describes the layer material
    where appropriate"""

    epsilonR: Optional[float] = None
    """The optional ``epsilonR`` token defines the dielectric constant of the layer material"""

    lossTangent: Optional[float] = None
    """The optional layer ``lossTangent`` token defines the dielectric loss tangent of the layer"""

    subLayers: List[StackupSubLayer] = field(default_factory=list)
    """The ``sublayers`` token defines a list of zero or more sublayers that are used to create
    stacks of dielectric layers. Does not apply to copper-type layers."""

    @classmethod
    def from_sexpr(cls, exp: list) -> StackupLayer:
        """Convert the given S-Expresstion into a StackupLayer object

        Args:
            - exp (list): Part of parsed S-Expression ``(layer ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not layer

        Returns:
            - StackupLayer: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'layer':
            raise Exception("Expression does not have the correct type")

        parsingSublayer = False
        tempSublayer = StackupSubLayer()
        object = cls()
        object.name = exp[1]
        for item in exp[2:]:
            if type(item) != type([]):
                # Start parsing the layer's sublayer if the first sublayer token was found
                if item == 'addsublayer':
                    if parsingSublayer:
                        # When the ``addsublayer`` token was found a second time, the previously
                        # parsed sublayer will be appended to the list of sublayers
                        object.subLayers.append(tempSublayer)
                        tempSublayer = StackupSubLayer()
                    else:
                        # Change state of the parser to look for StackupSubLayer tokens
                        parsingSublayer = True
                continue

            # Parse the tokens of StackupSubLayer for the current sublayer
            if parsingSublayer:
                if item[0] == 'thickness': tempSublayer.thickness = item[1]
                if item[0] == 'material': tempSublayer.material = item[1]
                if item[0] == 'epsilon_r': tempSublayer.epsilonR = item[1]
                if item[0] == 'loss_tangent': tempSublayer.lossTangent = item[1]
                continue

            # Parse the normal tokens of StackupLayer token
            if item[0] == 'type': object.type = item[1]
            if item[0] == 'thickness': object.thickness = item[1]
            if item[0] == 'material': object.material = item[1]
            if item[0] == 'epsilon_r': object.epsilonR = item[1]
            if item[0] == 'loss_tangent': object.lossTangent = item[1]
            if item[0] == 'color': object.color = item[1]

        # Add the last parsed sublayer to the list, if any
        if parsingSublayer:
            object.subLayers.append(tempSublayer)

        return object

    def to_sexpr(self, indent=6, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 6.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        color = f' (color "{dequote(self.color)}")' if self.color is not None else ''
        material = f' (material "{dequote(self.material)}")' if self.material is not None else ''
        thickness = f' (thickness {self.thickness})' if self.thickness is not None else ''
        epsilon_r = f' (epsilon_r {self.epsilonR})' if self.epsilonR is not None else ''
        loss_tangent = f' (loss_tangent {self.lossTangent})' if self.lossTangent is not None else ''

        expression = f'{indents}(layer "{dequote(self.name)}" (type "{self.type}"){color}{thickness}'
        expression +=f'{material}{epsilon_r}{loss_tangent}'
        for layer in self.subLayers:
            expression += f'\n{layer.to_sexpr(indent+2)}'
        expression += f'){endline}'
        return expression

@dataclass
class Stackup():
    """The ``stackup`` token defines the board stack up settings and is defined in the setup
    section.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/#_stack_up_settings
    """

    layers: List[StackupLayer] = field(default_factory=list)
    """The ``layers``token is a list of layer settings for each layer required to manufacture
    a board including the dielectric material between the actual layers defined in the board
    editor."""

    copperFinish: Optional[str] = None
    """The optional ``copperFinish`` token is a string that defines the copper finish used to
    manufacture the board"""

    dielectricContraints: Optional[str] = None
    """The optional ``dielectricContraints`` token define if the board should meet all
    dielectric requirements. Valid values are ``yes`` and ``no``."""

    edgeConnector: Optional[str] = None
    """The optional ``edgeConnector`` token defines if the board has an edge connector
    (value: ``yes``) and if the edge connector is bevelled (value: ``bevelled``)"""

    castellatedPads: bool = False
    """The ``castellatedPads`` token defines if the board edges contain castellated pads"""

    edgePlating: bool = False
    """The ``edgePlating`` token defines if the board edges should be plated."""

    @classmethod
    def from_sexpr(cls, exp: list) -> Stackup:
        """Convert the given S-Expresstion into a Stackup object

        Args:
            - exp (list): Part of parsed S-Expression ``(stackup ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not stackup

        Returns:
            - Stackup: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'stackup':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'layer': object.layers.append(StackupLayer().from_sexpr(item))
            if item[0] == 'copper_finish': object.copperFinish = item[1]
            if item[0] == 'dielectric_constraints': object.dielectricContraints = item[1]
            if item[0] == 'edge_connector': object.edgeConnector = item[1]
            if item[0] == 'castellated_pads': object.castellatedPads = True
            if item[0] == 'edge_plating': object.edgePlating = True
        return object

    def to_sexpr(self, indent=4, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 4.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        expression =  f'{indents}(stackup\n'
        for layer in self.layers:
            expression += layer.to_sexpr(indent+2)
        if self.copperFinish is not None:         expression += f'{indents}  (copper_finish "{dequote(self.copperFinish)}")\n'
        if self.dielectricContraints is not None: expression += f'{indents}  (dielectric_constraints {self.dielectricContraints})\n'
        if self.edgeConnector is not None:        expression += f'{indents}  (edge_connector {self.edgeConnector})\n'
        if self.castellatedPads:                  expression += f'{indents}  (castellated_pads yes)\n'
        if self.edgePlating:                      expression += f'{indents}  (edge_plating yes)\n'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class PlotSettings():
    """The ``pcbplotparams`` token defines the plotting and printing settings used for the last
    plot and is defined in the set up section.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/#_plot_settings
    """

    layerSelection: str = ""
    """The ``layerSelection`` token defines a hexadecimal bit set of the layers to plot"""

    plotOnAllLayersSelection: Optional[str] = None
    """The ``plotOnAllLayersSelection`` token defines a hexadecimal bit set of layers where all 
    selected layers shall be plotted.
    
    Available and required since KiCad v7"""

    disableApertMacros: bool = False
    """The ``disableApertMacros`` token defines if aperture macros are to be used in gerber plots"""

    useGerberExtensions: bool = False
    """The ``useGerberExtensions`` token  defines if the Protel layer file name extensions are to
    be used in gerber plots"""

    useGerberAttributes: bool = False
    """The ``useGerberAttributes`` token defines if the X2 extensions are used in gerber plots"""

    useGerberAdvancedAttributes: bool = False
    """The ``useGerberAdvancedAttributes`` token defines if the netlist information should be
    included in gerber plots"""

    createGerberJobFile: bool = False
    """The ``createGerberJobFile`` token defines if a job file should be created when plotting 
    gerber files"""

    # FIXME: Where is the docu of this token?
    dashedLineDashRatio: Optional[float] = None
    """The ``dashedLineDashRatio`` token's documentation is still missing ..
    
    Available and required since KiCad v7"""

    # FIXME: Where is the docu of this token?
    dashedLineGapRatio: Optional[float] = None
    """The ``dashedLineGapRatio`` token's documentation is still missing ..
    
    Available and required since KiCad v7"""

    svgUseInch: Optional[bool] = None
    """The ``svgUseInch`` token defines if inch units should be use when plotting SVG files.
    
    Required until KiCad v6, removed since KiCad v7"""

    svgPrecision: float = 0.0
    """The ``svgPrecision`` token defines the units precision used when plotting SVG files"""

    excludeEdgeLayer: Optional[bool] = None
    """The ``excludeEdgeLayer`` token defines if the board edge layer is plotted on all layers.
    
    Required until KiCad v6, removed since KiCad v7"""

    plotFameRef: bool = False
    """The ``plotFameRef`` token defines if the border and title block should be plotted"""

    viasOnMask: bool = False
    """The ``viasOnMask`` token defines if the vias are to be tented"""

    mode: int = 1
    """The ``mode`` token defines the plot mode. An attribute of 1 plots in the normal
    mode and an attribute of 2 plots in the outline (sketch) mode."""

    useAuxOrigin: bool = False
    """The ``useAuxOrigin`` token determines if all coordinates are offset by the defined user origin"""

    hpglPenNumber: int = 0
    """The ``hpglPenNumber`` token defines the integer pen number used for HPGL plots"""

    hpglPenSpeed: int = 0
    """The ``hpglPenSpeed`` token defines the integer pen speed used for HPGL plots"""

    hpglPenDiameter: float = 0.0
    """The ``hpglPenDiameter`` token defines the floating point pen size for HPGL plots"""

    dxfPolygonMode: bool = False
    """The ``dxfPolygonMode`` token defines if the polygon mode should be used for DXF plots"""

    dxfImperialUnits: bool = False
    """The ``dxfImperialUnits`` token defines if imperial units should be used for DXF plots"""

    dxfUsePcbnewFont: bool = False
    """The ``dxfUsePcbnewFont`` token defines if the Pcbnew font (vector font) or the default
    font should be used for DXF plots"""

    psNegative: bool = False
    """The ``psNegative`` token defines if the output should be the negative for PostScript plots"""

    psA4Output: bool = False
    """The ``psA4Output`` token defines if the A4 page size should be used for PostScript plots"""

    plotReference: bool = False
    """The ``plotReference`` token defines if hidden reference field text should be plotted"""

    plotValue: bool = False
    """The ``plotValue`` token defines if hidden value field text should be plotted"""

    plotInvisibleText: bool = False
    """The ``plotInvisibleText`` token defines if hidden text other than the reference and
    value fields should be plotted"""

    sketchPadsOnFab: bool = False
    """The ``sketchPadsOnFab`` token defines if pads should be plotted in the outline (sketch) mode"""

    subtractMaskFromSilk: bool = False
    """The ``subtractMaskFromSilk`` token defines if the solder mask layers should be subtracted from
    the silk screen layers for gerber plots"""

    outputFormat: int = 0
    """The ``outputFormat`` token defines the last plot type. The following values are defined:
    - 0: gerber
    - 1: PostScript
    - 2: SVG
    - 3: DXF
    - 4: HPGL
    - 5: PDF"""

    mirror: bool = False
    """The ``mirror`` token defines if the plot should be mirrored"""

    drillShape: int = 0
    """The ``drillShape`` token defines the type of drill marks used for drill files"""

    scaleSelection: int = 1
    """The ``scaleSelection`` is not documented yet (as of 20.02.2022)"""

    outputDirectory: str = ""
    """The ``drillShape`` token defines the path relative to the current project path
    where the plot files will be saved"""

    pdfFrontFpPropertyPopups: bool = False
    """Generate property popups for front footprints: When enabled, interactive popups will be added
    to the generated PDF containing part information for each footprint on the front of the board."""

    pdfBackFpPropertyPopups: bool = False
    """Generate property popups for back footprints: When enabled, interactive popups will be added
    to the generated PDF containing part information for each footprint on the back of the board."""

    plotFpText: bool = False
    """Indicates if footprint text should be printed to output"""

    @classmethod
    def from_sexpr(cls, exp: list) -> PlotSettings:
        """Convert the given S-Expresstion into a PlotSettings object

        Args:
            - exp (list): Part of parsed S-Expression ``(pcbplotparams ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not pcbplotparams

        Returns:
            - PlotSettings: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'pcbplotparams':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'layerselection': object.layerSelection = item[1]
            if item[0] == 'plot_on_all_layers_selection': object.plotOnAllLayersSelection = item[1]
            if item[0] == 'disableapertmacros': object.disableApertMacros = sexpr.parse_bool(item)
            if item[0] == 'usegerberextensions' : object.useGerberExtensions = sexpr.parse_bool(item)
            if item[0] == 'usegerberattributes' : object.useGerberAttributes = sexpr.parse_bool(item)
            if item[0] == 'usegerberadvancedattributes' : object.useGerberAdvancedAttributes = sexpr.parse_bool(item)
            if item[0] == 'creategerberjobfile' : object.createGerberJobFile = sexpr.parse_bool(item)
            if item[0] == 'dashed_line_dash_ratio': object.dashedLineDashRatio = item[1]
            if item[0] == 'dashed_line_gap_ratio': object.dashedLineGapRatio = item[1]
            if item[0] == 'svguseinch' : object.svgUseInch = sexpr.parse_bool(item)
            if item[0] == 'svgprecision' : object.svgPrecision = item[1]
            if item[0] == 'excludeedgelayer' : object.excludeEdgeLayer = sexpr.parse_bool(item)
            if item[0] == 'plotframeref' : object.plotFameRef = sexpr.parse_bool(item)
            if item[0] == 'viasonmask' : object.viasOnMask = sexpr.parse_bool(item)
            if item[0] == 'mode' : object.mode = item[1]
            if item[0] == 'useauxorigin' : object.useAuxOrigin = sexpr.parse_bool(item)
            if item[0] == 'hpglpennumber' : object.hpglPenNumber = item[1]
            if item[0] == 'hpglpenspeed' : object.hpglPenSpeed = item[1]
            if item[0] == 'hpglpendiameter' : object.hpglPenDiameter = item[1]
            if item[0] == 'dxfpolygonmode' : object.dxfPolygonMode = sexpr.parse_bool(item)
            if item[0] == 'dxfimperialunits' : object.dxfImperialUnits = sexpr.parse_bool(item)
            if item[0] == 'dxfusepcbnewfont' : object.dxfUsePcbnewFont = sexpr.parse_bool(item)
            if item[0] == 'psnegative' : object.psNegative = sexpr.parse_bool(item)
            if item[0] == 'psa4output' : object.psA4Output = sexpr.parse_bool(item)
            if item[0] == 'plotreference' : object.plotReference = sexpr.parse_bool(item)
            if item[0] == 'plotvalue' : object.plotValue = sexpr.parse_bool(item)
            if item[0] == 'plotinvisibletext' : object.plotInvisibleText = sexpr.parse_bool(item)
            if item[0] == 'sketchpadsonfab' : object.sketchPadsOnFab = sexpr.parse_bool(item)
            if item[0] == 'subtractmaskfromsilk' : object.subtractMaskFromSilk = sexpr.parse_bool(item)
            if item[0] == 'outputformat' : object.outputFormat = item[1]
            if item[0] == 'mirror' : object.mirror = sexpr.parse_bool(item)
            if item[0] == 'drillshape' : object.drillShape = item[1]
            if item[0] == 'scaleselection' : object.scaleSelection = item[1]
            if item[0] == 'outputdirectory' : object.outputDirectory = item[1]
            if item[0] == 'pdf_front_fp_property_popups' : object.pdfFrontFpPropertyPopups = sexpr.parse_bool(item)
            if item[0] == 'pdf_back_fp_property_popups' : object.pdfBackFpPropertyPopups = sexpr.parse_bool(item)
            if item[0] == 'plotfptext' : object.plotFpText  = sexpr.parse_bool(item)
        return object

    def to_sexpr(self, indent=4, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 4.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        bools = ('no','yes')

        expression =  f'{indents}(pcbplotparams\n'
        expression += f'{indents}  (layerselection {self.layerSelection})\n'
        if self.plotOnAllLayersSelection is not None:
            expression += f'{indents}  (plot_on_all_layers_selection {self.plotOnAllLayersSelection})\n'
        expression += f'{indents}  (disableapertmacros {bools[self.disableApertMacros]})\n'
        expression += f'{indents}  (usegerberextensions {bools[self.useGerberExtensions]})\n'
        expression += f'{indents}  (usegerberattributes {bools[self.useGerberAttributes]})\n'
        expression += f'{indents}  (usegerberadvancedattributes {bools[self.useGerberAdvancedAttributes]})\n'
        expression += f'{indents}  (creategerberjobfile {bools[self.createGerberJobFile]})\n'
        if self.dashedLineDashRatio is not None:
            expression += f'{indents}  (dashed_line_dash_ratio {float(self.dashedLineDashRatio):.6f})\n'
        if self.dashedLineGapRatio is not None:
            expression += f'{indents}  (dashed_line_gap_ratio {float(self.dashedLineGapRatio):.6f})\n'
        if self.svgUseInch is not None:
            expression += f'{indents}  (svguseinch {bools[self.svgUseInch]})\n'
        expression += f'{indents}  (svgprecision {self.svgPrecision})\n'
        if self.excludeEdgeLayer is not None:
            expression += f'{indents}  (excludeedgelayer {bools[self.excludeEdgeLayer]})\n'
        expression += f'{indents}  (plotframeref {bools[self.plotFameRef]})\n'
        expression += f'{indents}  (viasonmask {bools[self.viasOnMask]})\n'
        expression += f'{indents}  (mode {self.mode})\n'
        expression += f'{indents}  (useauxorigin {bools[self.useAuxOrigin]})\n'
        expression += f'{indents}  (hpglpennumber {self.hpglPenNumber})\n'
        expression += f'{indents}  (hpglpenspeed {self.hpglPenSpeed})\n'
        expression += f'{indents}  (hpglpendiameter {float(self.hpglPenDiameter):.6f})\n'
        expression += f'{indents}  (pdf_front_fp_property_popups {bools[self.pdfFrontFpPropertyPopups]})'
        expression += f'{indents}  (pdf_back_fp_property_popups {bools[self.pdfBackFpPropertyPopups]})'
        expression += f'{indents}  (dxfpolygonmode {bools[self.dxfPolygonMode]})\n'
        expression += f'{indents}  (dxfimperialunits {bools[self.dxfImperialUnits]})\n'
        expression += f'{indents}  (dxfusepcbnewfont {bools[self.dxfUsePcbnewFont]})\n'
        expression += f'{indents}  (psnegative {bools[self.psNegative]})\n'
        expression += f'{indents}  (psa4output {bools[self.psA4Output]})\n'
        expression += f'{indents}  (plotreference {bools[self.plotReference]})\n'
        expression += f'{indents}  (plotvalue {bools[self.plotValue]})\n'
        expression += f'{indents}  (plotfptext {bools[self.plotFpText]})\n'
        expression += f'{indents}  (plotinvisibletext {bools[self.plotInvisibleText]})\n'
        expression += f'{indents}  (sketchpadsonfab {bools[self.sketchPadsOnFab]})\n'
        expression += f'{indents}  (subtractmaskfromsilk {bools[self.subtractMaskFromSilk]})\n'
        expression += f'{indents}  (outputformat {self.outputFormat})\n'
        expression += f'{indents}  (mirror {bools[self.mirror]})\n'
        expression += f'{indents}  (drillshape {self.drillShape})\n'
        expression += f'{indents}  (scaleselection {self.scaleSelection})\n'
        expression += f'{indents}  (outputdirectory "{dequote(self.outputDirectory)}")\n'
        expression += f'{indents}){endline}'
        return expression


@dataclass
class SetupData():
    """The setup token is used to store the current settings such as default item sizes and
    other options used by the board

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/#_setup_section
    """

    stackup: Optional[Stackup] = None
    """The optional ``stackup`` define the parameters required to manufacture the board"""

    packToMaskClearance: float = 0.0
    """The ``packToMaskClearance`` token defines the clearance between footprint pads and
    the solder mask"""

    solderMaskMinWidth: Optional[float] = None
    """The optional ``solderMaskMinWidth`` defines the minimum solder mask width. If not
    defined, the minimum width is zero."""

    padToPasteClearance: Optional[float] = None
    """The optional ``padToPasteClearance`` defines the clearance between footprint pads
    and the solder paste layer. If not defined, the clearance is zero"""

    padToPasteClearanceRatio: Optional[float] = None
    """The optional ``padToPasteClearanceRatio`` is the percentage (from 0 to 100) of the
    footprint pad to make the solder paste. If not defined, the ratio is 100% (the same
    size as the pad)."""

    auxAxisOrigin: Optional[Position] = None
    """The optional ``auxAxisOrigin`` defines the auxiliary origin if it is set to anything
    other than (0,0)."""

    gridOrigin: Optional[Position] = None
    """The optional ``gridOrigin`` defines the grid original if it is set to anything other
    than (0,0)."""

    plotSettings: Optional[PlotSettings] = None
    """The optional ``plotSettings`` define how the board was last plotted."""

    allowSoldermaskBridgesInFootprints: Optional[bool] = None
    """Inidcates if footprints on board are allowed to have pads bridged with soldermask"""

    @classmethod
    def from_sexpr(cls, exp: list) -> SetupData:
        """Convert the given S-Expresstion into a SetupData object

        Args:
            - exp (list): Part of parsed S-Expression ``(setup ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not setup

        Returns:
            - SetupData: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'setup':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'stackup': object.stackup = Stackup().from_sexpr(item)
            if item[0] == 'pcbplotparams': object.plotSettings = PlotSettings().from_sexpr(item)
            if item[0] == 'pad_to_mask_clearance': object.packToMaskClearance = item[1]
            if item[0] == 'allow_soldermask_bridges_in_footprints': object.allowSoldermaskBridgesInFootprints = sexpr.parse_bool(item)
            if item[0] == 'solder_mask_min_width': object.solderMaskMinWidth = item[1]
            if item[0] == 'pad_to_paste_clearance': object.padToPasteClearance = item[1]
            if item[0] == 'pad_to_paste_clearance_ratio': object.padToPasteClearanceRatio = item[1]
            if item[0] == 'aux_axis_origin': object.auxAxisOrigin = Position().from_sexpr(item)
            if item[0] == 'grid_origin': object.gridOrigin = Position().from_sexpr(item)
            if item[0] == 'pcbplotparams': object.plotSettings = PlotSettings().from_sexpr(item)
        return object

    def to_sexpr(self, indent=2, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        expression =  f'{indents}(setup\n'
        if self.stackup is not None:                  expression += self.stackup.to_sexpr(indent+2)
        expression += f'{indents}  (pad_to_mask_clearance {self.packToMaskClearance})\n'
        if self.solderMaskMinWidth is not None:                   expression += f'{indents}  (solder_mask_min_width {self.solderMaskMinWidth})\n'
        if self.padToPasteClearance is not None:                  expression += f'{indents}  (pad_to_paste_clearance {self.padToPasteClearance})\n'
        if self.allowSoldermaskBridgesInFootprints is not None:   expression += f'{indents}  (allow_soldermask_bridges_in_footprints {"yes" if self.allowSoldermaskBridgesInFootprints else "no"} )'
        if self.padToPasteClearanceRatio is not None:             expression += f'{indents}  (pad_to_paste_clearance_ratio {self.padToPasteClearanceRatio})\n'
        if self.auxAxisOrigin is not None:                        expression += f'{indents}  (aux_axis_origin {self.auxAxisOrigin.X} {self.auxAxisOrigin.Y})\n'
        if self.gridOrigin is not None:                           expression += f'{indents}  (grid_origin {self.gridOrigin.X} {self.gridOrigin.Y})\n'
        if self.plotSettings is not None:                         expression += self.plotSettings.to_sexpr(indent+2)
        expression += f'{indents}){endline}'
        return expression


@dataclass
class Segment():
    """The ``segment`` token defines a track segment in a KiCad board

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/#_track_segment
    """

    start: Position = field(default_factory=lambda: Position())
    """The ``start`` token defines the coordinates of the beginning of the line"""

    end: Position = field(default_factory=lambda: Position())
    """The ``end`` token defines the coordinates of the end of the line"""

    width: float = 0.1
    """The ``width`` token defines the line width"""

    layer: str = "F.Cu"
    """The ``layer`` token defines the canonical layer the track segment resides on"""

    locked: bool = False
    """The ``locked`` token defines if the line cannot be edited"""

    net: int = 0
    """The ``net`` token defines by the net ordinal number which net in the net
    section that the segment is part of"""
    
    uuid: Optional[str] =""
    """The optional ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Segment:
        """Convert the given S-Expresstion into a Segment object

        Args:
            - exp (list): Part of parsed S-Expression ``(segment ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not segment

        Returns:
            - Segment: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'segment':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            if item[0] == 'start': object.start = Position().from_sexpr(item)
            if item[0] == 'end': object.end = Position().from_sexpr(item)
            if item[0] == 'width': object.width = item[1]
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'net': object.net = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
        return object

    def to_sexpr(self, indent=2, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        locked = '( locked yes )' if self.locked else ''

        return f'{indents}(segment{locked} (start {self.start.X} {self.start.Y}) (end {self.end.X} {self.end.Y}) (width {self.width}) (layer "{dequote(self.layer)}") (net {self.net}) (uuid "{dequote(self.uuid)}")){endline}'


@dataclass
class Generated:
    """Class represents editable trace tunning object (introduced in KiCad 8)"""

    uuid: str = ""
    """The ``uuid`` defines the universally unique identifier"""

    type: str = ""
    """The ``type`` token defines the type of the tuned track """

    name: str = ""
    """The ``name`` token defines the name of the tuned track"""

    layer: str = "F.Cu"
    """The ``layer`` token defines the canonical layer the tuned track resides on"""

    baseLine: List[str] = field(default_factory=list)
    """The ``baseLine`` token defines a primary line that tuned tracks are alligned to"""

    baseLineCoupled: List[str] = field(default_factory=list)
    """The ``baseLineCoupled`` token defines the coupled base line of the tuned tracks"""

    cornerRadius: int = 0
    """The ``cornerRadius`` token defines the radius of the corner"""

    end: str = ""
    """The ``end`` token defines the end of the tuned track"""

    initialSide: str = ""
    """The ``initialSide`` token defines the initial side of the tuned track"""

    lastDiffPairGap: float = 0
    """The ``lastDiffPairGap`` token holds the value of the last used differential pair gap"""

    lastNetName: str = ""
    """The ``lastNetName`` token holds the last used net name"""

    lastStatus: str = ""
    """The ``lastStatus`` token holds the last status of the tuned track"""

    lastTrackWidth: float = 0
    """The ``lastTrackWidth`` token holds the last width of the tuned track"""

    lastTuning: str = ""
    """The ``lastTuning`` token holds the last tuning of the tuned track"""

    maxAmplitude: float = 0
    """The ``maxAmplitude`` token defines the maximal amplitude of the tuned track"""

    minAmplitude: float = 0
    """The ``minAmplitude`` token defines the minimal amplitude of the tuned track"""

    minSpacing: float = 0
    """The ``minSpacing`` token defines the minimal spacing of the tuned track"""

    origin: str = ""
    """The ``origin`` token defines the origin of the tuned track"""

    overrideCustomRules: str = ""
    """The ``overrideCustomRules`` token enables to bypass the custom rules"""

    rounded: str = ""
    """The ``rounded`` token defines if the tuned track is rounded"""

    singleSided: str = ""
    """The ``singleSided`` token defines if the tuned track is single sided"""

    targetLength: float = 0
    """The ``targetLength`` token defines the target length of the tuned track"""

    targetLengthMax: float = 0
    """The ``targetLengthMax`` token defines the maximal length of the tuned track"""

    targetLengthMin: float = 0
    """The ``targetLengthMin`` token defines the minimal length of the tuned track"""

    targetSkew: float = 0
    """The ``targetSkew`` token defines the target skew of the tuned track"""

    targetSkewMax: float = 0
    """The ``targetSkewMax`` token defines the maximal target skew of the tuned track"""

    targetSkewMin: float = 0
    """The ``targetSkewMin`` token defines the minimal target skew of the tuned track"""

    tuningMode: str = ""
    """The ``tuningMode`` token defines the mode of tuning the tuned track"""

    members: List[str] = field(default_factory=list)
    """The ``members`` token defines the members of the tuned track"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Generated:
        """Convert the given S-Expresstion into a ``Generated`` object

        Args:
            - exp (list): Part of parsed S-Expression ``(generated ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not ``generated``

        Returns:
            - ``Generated``: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != "generated":
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == "uuid":
                object.uuid = item[1]
            elif item[0] == "type":
                object.type = item[1]
            elif item[0] == "name":
                object.name = item[1]
            elif item[0] == "layer":
                object.layer = item[1]
            elif item[0] == "base_line":
                pts = item[1]
                if pts[0] == "pts":
                    for point in pts[1:]:
                        object.baseLine.append(point)
            elif item[0] == "base_line_coupled":
                pts = item[1]
                if pts[0] == "pts":
                    for point in pts[1:]:
                        object.baseLineCoupled.append(point)
            elif item[0] == "corner_radius_percent":
                object.cornerRadius = item[1]
            elif item[0] == "end":
                object.end = item[1]
            elif item[0] == "initial_side":
                object.initialSide = item[1]
            elif item[0] == "initial_side":
                object.initialSide = item[1]
            elif item[0] == "last_diff_pair_gap":
                object.lastDiffPairGap = item[1]
            elif item[0] == "last_netname":
                object.lastNetName = item[1]
            elif item[0] == "last_status":
                object.lastStatus = item[1]
            elif item[0] == "last_track_width":
                object.lastTrackWidth = item[1]
            elif item[0] == "last_tuning":
                object.lastTuning = item[1]
            elif item[0] == "max_amplitude":
                object.maxAmplitude = item[1]
            elif item[0] == "min_amplitude":
                object.minAmplitude = item[1]
            elif item[0] == "min_spacing":
                object.minSpacing = item[1]
            elif item[0] == "origin":
                object.origin = item[1]
            elif item[0] == "override_custom_rules":
                object.overrideCustomRules = item[1]
            elif item[0] == "rounded":
                object.rounded = item[1]
            elif item[0] == "single_sided":
                object.singleSided = item[1]
            elif item[0] == "target_length":
                object.targetLength = item[1]
            elif item[0] == "target_length_max":
                object.targetLengthMax = item[1]
            elif item[0] == "target_length_min":
                object.targetLengthMin = item[1]
            elif item[0] == "target_skew":
                object.targetSkew = item[1]
            elif item[0] == "target_skew_max":
                object.targetSkewMax = item[1]
            elif item[0] == "target_skew_min":
                object.targetSkewMin = item[1]
            elif item[0] == "tuning_mode":
                object.tuningMode = item[1]
            elif item[0] == "members":
                for member in item[1:]:
                    object.members.append(member)
        return object

    def generate_xy(self, xy) -> str:
        """Serialize (to S-expr) list of points"""
        expression = ""
        for p in xy:
            expression += f" ({dequote(p[0])} {p[1]} {p[2]})"
        return expression

    def to_sexpr(self, indent=2, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = " " * indent
        endline = "\n" if newline else ""
        baseLine = f"(base_line (pts{self.generate_xy(self.baseLine)}))"
        baseLineCoupled = f"(base_line_coupled (pts{self.generate_xy(self.baseLineCoupled)}))"
        end = f"(end ({self.end[0]} {self.end[1]} {self.end[2]}))"
        origin = f"(origin ({self.origin[0]} {self.origin[1]} {self.origin[2]}))"
        # create members list
        members = f"{endline}(members"
        for member in self.members:
            members += f"{endline}{indents}{dequote(member)}"
        members += f"{endline})"

        expression = f"{indents}(generated"
        expression += f'{endline}{indents}(uuid "{dequote(self.uuid)}")'
        expression += f"{endline}{indents}(type {self.type})"
        expression += f'{endline}{indents}(name "{dequote(self.name)}")'
        expression += f'{endline}{indents}(layer "{dequote(self.layer)}")'
        expression += f"{endline}{indents}{baseLine}"
        expression += f"{endline}{indents}{baseLineCoupled}"
        expression += f"{endline}{indents}(corner_radius_percent {self.cornerRadius})"
        expression += f"{endline}{indents}{end}"
        expression += f'{endline}{indents}(initial_side "{dequote(self.initialSide)}")'
        expression += f"{endline}{indents}(last_diff_pair_gap {self.lastDiffPairGap})"
        expression += f'{endline}{indents}(last_netname "{dequote(self.lastNetName)}")'
        expression += f'{endline}{indents}(last_status "{dequote(self.lastStatus)}")'
        expression += f"{endline}{indents}(last_track_width {self.lastTrackWidth})"
        expression += f'{endline}{indents}(last_tuning "{dequote(self.lastTuning)}")'
        expression += f"{endline}{indents}(max_amplitude {self.maxAmplitude})"
        expression += f"{endline}{indents}(min_amplitude {self.minAmplitude})"
        expression += f"{endline}{indents}(min_spacing {self.minSpacing})"
        expression += f"{endline}{indents}{origin}"
        expression += f"{endline}{indents}(override_custom_rules {self.overrideCustomRules})"
        expression += f"{endline}{indents}(rounded {self.rounded})"
        expression += f"{endline}{indents}(single_sided {self.singleSided})"
        expression += f"{endline}{indents}(target_length {self.targetLength})"
        expression += f"{endline}{indents}(target_length_max {self.targetLengthMax})"
        expression += f"{endline}{indents}(target_length_min {self.targetLengthMin})"
        expression += f"{endline}{indents}(target_skew {self.targetSkew})"
        expression += f"{endline}{indents}(target_skew_max {self.targetSkewMax})"
        expression += f"{endline}{indents}(target_skew_min {self.targetSkewMin})"
        expression += f'{endline}{indents}(tuning_mode "{dequote(self.tuningMode)}")'
        expression += f"{members}"
        expression += f"{endline}{indents})"

        return expression


@dataclass
class Via():
    """The ``via`` token defines a track via in a KiCad board

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/#_track_via
    """

    type: Optional[str] = None
    """The optional ``type`` attribute specifies the via type. Valid via types are ``blind`` and
    ``micro``. If no type is defined, the via is a through hole type"""

    locked: bool = False
    """The ``locked`` token defines if the line cannot be edited"""

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` token define the coordinates of the center of the via"""

    size: float = 0.0
    """The ``size`` token define the diameter of the via annular ring"""

    drill: float = 0.0
    """The ``drill`` token define the drill diameter of the via"""

    layers: List[str] = field(default_factory=list)
    """The ``layers`` token define the canonical layer set the via connects as a list
    of strings"""

    removeUnusedLayers: Optional[bool] = None
    """The ``removeUnusedLayers`` token is undocumented (as of 20.02.2022)"""

    keepEndLayers: Optional[bool] = None
    """The ``keepEndLayers`` token is undocumented (as of 20.02.2022)"""

    free: Optional[bool] = None
    """The ``free`` token indicates that the via is free to be moved outside it's assigned net"""

    net: int = 0
    """The ``net`` token defines by net ordinal number which net in the net section that
    the via is part of"""

    uuid: Optional[str] =""
    """The optional ``uuid`` defines the universally unique identifier"""

    zoneLayerConnections: Optional[List[str]] = None
    """Indicates which cooper layers are connected"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Via:
        """Convert the given S-Expresstion into a Via object

        Args:
            - exp (list): Part of parsed S-Expression ``(via ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not via

        Returns:
            - Via: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'via':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if type(item) != type([]):
                if item == 'micro' or item == 'blind': object.type = item
                continue
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'size': object.size = item[1]
            if item[0] == 'drill': object.drill = item[1]
            if item[0] == 'layers':
                for layer in item[1:]:
                    object.layers.append(layer)
            if item[0] == 'remove_unused_layers': object.removeUnusedLayers = sexpr.parse_bool(item)
            if item[0] == 'keep_end_layers': object.keepEndLayers = sexpr.parse_bool(item)
            if item[0] == 'free': object.free = sexpr.parse_bool(item)
            if item[0] == 'net': object.net = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'zone_layer_connections':
                object.zoneLayerConnections = []
                for layer in item[1:]:
                    object.zoneLayerConnections.append(layer)

        return object

    def to_sexpr(self, indent=2, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        type = f' {self.type}' if self.type is not None else ''
        locked = f'( locked yes )' if self.locked else ''

        layers = ''
        for layer in self.layers:
            layers += f' "{dequote(layer)}"'


        remove_unused_layers = ""
        keep_end_layers = ""
        zone_layer_connections = ''
        free = ""
        if self.removeUnusedLayers is not None:
            remove_unused_layers = (
                f" (remove_unused_layers yes)"
                if self.removeUnusedLayers
                else " (remove_unused_layers no)"
            )
        if self.keepEndLayers is not None:
            keep_end_layers = (
                f" (keep_end_layers yes)"
                if self.keepEndLayers
                else " (keep_end_layers no)"
            )
        if self.zoneLayerConnections is not None:
            zone_layer_connections += ' (zone_layer_connections'
            for layer in self.zoneLayerConnections:
                zone_layer_connections += f' "{dequote(layer)}"'
            zone_layer_connections += ')'
        if self.free is not None:
            free = f" (free yes)" if self.free else " (free no)"
        uuid = f' (uuid "{dequote(self.uuid)}")' if self.uuid is not None else ''

        return f'{indents}(via{type}{locked} (at {self.position.X} {self.position.Y}) (size {self.size}) (drill {self.drill}) (layers{layers}){remove_unused_layers}{keep_end_layers}{free} {zone_layer_connections}(net {self.net}){uuid}){endline}'

@dataclass
class Arc():
    """The ``arc`` token defines a track arc, which will be generated when using the length-matching
    feature on differential pairs.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/#_track_arc
    """

    start: Position = field(default_factory=lambda: Position())
    """The ``start`` token defines the coordinates of the beginning of the arc"""

    mid: Position = field(default_factory=lambda: Position())
    """The ``mid`` token defines the coordinates of the mid point of the radius of the arc"""

    end: Position = field(default_factory=lambda: Position())
    """The ``end`` token defines the coordinates of the end of the arc"""

    width: float = 0.2
    """The ``width`` token defines the line width of the arc. Defaults to 0,2."""

    layer: str = "F.Cu"
    """The ``layer`` token defiens the canonical layer the track arc resides on. Defaults to `F.Cu`."""

    locked: bool = False
    """The ``locked`` token defines if the arc cannot be edited. Defaults to False."""

    net: int = 0
    """The ``net`` token defines the net ordinal number which net in the net section that arc is part
    of. Defaults to 0."""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Arc:
        """Convert the given S-Expresstion into a Arc object

        Args:
            - exp (list): Part of parsed S-Expression ``(arc ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not ``arc``

        Returns:
            - Arc: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'arc':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            elif item[0] == 'start': object.start = Position().from_sexpr(item)
            elif item[0] == 'mid': object.mid = Position().from_sexpr(item)
            elif item[0] == 'end': object.end = Position().from_sexpr(item)
            elif item[0] == 'width': object.width = item[1]
            elif item[0] == 'layer': object.layer = item[1]
            elif item[0] == 'net': object.net = item[1]
            elif item[0] == 'uuid': object.uuid = item[1]
        return object

    def to_sexpr(self, indent=2, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        locked = f'( locked yes )' if self.locked else ''
        uuid = f' (uuid "{dequote(self.uuid)}")' if self.uuid is not None else ''

        expression = f'{indents}(arc{locked} (start {self.start.X} {self.start.Y}) '
        expression += f'(mid {self.mid.X} {self.mid.Y}) (end {self.end.X} {self.end.Y}) '
        expression += f'(width {self.width}) (layer "{dequote(self.layer)}") '
        expression += f'(net {self.net}){uuid}){endline}'
        return expression

@dataclass
class Target():
    """The ``target`` token defines a target marker on the PCB

    Documentation:
        Not found in KiCad docu - 15.06.2022
    """

    type: str = "plus"
    """The ``type`` token specifies the shape of the marker. Valid types are ``plus`` and ``x``."""

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` token specifies the position of the target marker"""

    size: float = 0
    """The ``size`` token sets the marker's size"""

    width: float = 0.1
    """The ``width`` token sets the marker's line width"""

    layer: str = "F.Cu"
    """The ``layer`` token sets the canonical layer where the target marker resides"""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Target:
        """Convert the given S-Expresstion into a Target object

        Args:
            - exp (list): Part of parsed S-Expression ``(target ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not target

        Returns:
            - Target: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'target':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.type = exp[1]
        for item in exp[2:]:
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'size': object.size = item[1]
            if item[0] == 'width': object.width = item[1]
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
        return object

    def to_sexpr(self, indent=2, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        return f'{indents}(target {self.type} (at {self.position.X} {self.position.Y}) (size {self.size}) (width {self.width}) (layer "{self.layer}") (uuid "{dequote(self.uuid)}")){endline}'
