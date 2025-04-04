"""The graphical items are footprint and board items that are outside of the connectivity items.
   This includes graphical items on technical, user, and copper layers. Graphical items are also
   used to define complex pad geometries.

Author:
    (C) Marvin Mager - @mvnmgrx - 2022

License identifier:
    GPL-3.0

Major changes:
    10.02.2022 - created

Documentation taken from:
    https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphic_items
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, ClassVar, cast

from kiutils.items.common import Effects, Position, RenderCache, Stroke, Coordinate2D, PositionEnd, PositionStart
from kiutils.utils.strings import dequote
from kiutils.utils import sexpr
from kiutils.utils.sexpr import SexprAuto

@dataclass
class GrText():
    """The ``gr_text`` token defines a graphical text.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_text
    """

    text: str = ""
    """The ``text`` attribute is a string that defines the text"""

    knockout: bool = False
    """The ``knockout`` token defines if the text is inverted (means transparent text and colored
    background insted of colored text and transparent background)"""

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` defines the X and Y position coordinates and optional orientation angle of 
    the text"""

    layer: Optional[str] = None
    """The ``layer`` token defines the canonical layer the text resides on"""

    effects: Effects = field(default_factory=lambda: Effects())
    """The ``effects`` token defines how the text is displayed"""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    locked: bool = False
    """The ``locked`` token defines if the object may be moved or not"""

    renderCache: Optional[RenderCache] = None
    """If the ``effects`` token prescribe a TrueType font then the optional ``render_cache`` token 
    should be given in case the font can not be found on the current system.
    
    Available since KiCad v7"""

    @classmethod
    def from_sexpr(cls, exp: list) -> GrText:
        """Convert the given S-Expresstion into a GrText object

        Args:
            - exp (list): Part of parsed S-Expression ``(gr_text ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not gr_text

        Returns:
            - GrText: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'gr_text':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.text = exp[1]
        for item in exp[2:]:
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'layer': 
                object.layer = item[1]
                if(len(item) > 2):
                    if(item[2] == "knockout"):
                        object.knockout = True
            if item[0] == 'effects': object.effects = Effects().from_sexpr(item)
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'render_cache': object.renderCache = RenderCache.from_sexpr(item)
        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        ko = ' knockout' if self.knockout else ''
        posA = f' {self.position.angle}' if self.position.angle is not None else ''
        layer =  f' (layer "{dequote(self.layer)}"{ko})' if self.layer is not None else ''
        uuid = f' ( uuid "{dequote(self.uuid)}" )' if self.uuid is not None else ''
        locked = f' (locked yes)' if self.locked else ''

        expression =  f'{indents}(gr_text "{dequote(self.text)}"{locked} (at {self.position.X} {self.position.Y}{posA}){layer}{uuid}\n'
        expression += f'{indents}  {self.effects.to_sexpr()}'
        if self.renderCache is not None:
            expression += self.renderCache.to_sexpr(indent+2)
        expression += f'{indents}){endline}'
        return expression

@dataclass
class GrTextBox(SexprAuto):
    """The ``gr_text_box`` token defines a graphical rectangle containing line-wrapped text.

    Available since KiCad v7
    
    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_text_box
    """
    sexpr_prefix: ClassVar[str] = "gr_text_box"
    positional_args: ClassVar[List[str]] = ["text"]
    

    text: str = ""
    """The ``text`` token defines the content of the text box. Defaults to an empty string."""

    locked: Optional[bool] = None
    """The ``locked`` token specifies if the text box can be moved. Defaults to ``False``."""

    start: Optional[PositionStart] = None
    """The optional ``start`` token defines the top-left of a cardinally oriented text box"""

    end: Optional[PositionEnd] = None
    """The optional ``end`` token defines the bottom-right of a cardinally oriented text box"""

    margins: List[float] = field(default_factory=list)

    pts: List[Coordinate2D] = field(default_factory=list)
    """The ``pts`` token defines the four corners of a non-cardianlly oriented text box. The corners
    must be in order, but the winding can be either direction."""

    angle: Optional[float] = None
    """The optional ``angle`` token defines the rotation of the text box in degrees.

    Note:
        - If ``angle`` is not given, or is a cardinal angle (0, 90, 180 or 270), then the text box
          MUST have ``start`` and ``end`` tokens.
        - If ``angle`` is given and is not a cardinal angle, then the text box MUST have a ``pts``
          token (with 4 pts).
    """

    layer: str = "F.Cu"
    """The ``layer`` token defines the canonical layer the text box resides on. Defaults to
    ``F.Cu``."""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    effects: Optional[Effects] = None
    """The optional ``effects`` token describes the style of the text in the text box"""

    border: Optional[bool] = None

    stroke: Optional[Stroke] = None
    """The optional ``stroke`` token describes the style of an optional border to be drawn around 
    the text box"""

    render_cache: Optional[RenderCache] = None
    """If the ``effects`` token prescribe a TrueType font then the optional ``render_cache`` token 
    should be given in case the font can not be found on the current system.
    
    Available since KiCad v7"""


@dataclass
class GrLine():
    """The ``gr_line`` token defines a graphical line.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_line
    """

    start: Position = field(default_factory=lambda: Position())
    """The ``start`` token defines the coordinates of the start of the line"""

    end: Position = field(default_factory=lambda: Position())
    """The ``end`` token defines the coordinates of the end of the line"""

    angle: Optional[float] = None
    """The optional ``angle`` token defines the rotational angle of the line"""

    layer: Optional[str] = None
    """The ``layer`` token defines the canonical layer the rectangle resides on"""

    width: Optional[float] = None     # Used for KiCad < 7
    """The ``width`` token defines the line width of the rectangle. (prior to version 7)"""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    locked: bool = False
    """The ``locked`` token defines if the object may be moved or not"""

    stroke: Optional[Stroke] = None
    """The optional ``stroke`` token describes the style of an optional border to be drawn around 
    the text box"""

    @classmethod
    def from_sexpr(cls, exp: list) -> GrLine:
        """Convert the given S-Expresstion into a GrLine object

        Args:
            - exp (list): Part of parsed S-Expression ``(gr_line ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not gr_line

        Returns:
            - GrLine: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'gr_line':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            if item[0] == 'start': object.start = Position.from_sexpr(item)
            if item[0] == 'end': object.end = Position.from_sexpr(item)
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'width': object.width = item[1]
            if item[0] == 'stroke': object.stroke = Stroke().from_sexpr(item)
        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        locked = f'(locked yes)' if self.locked else ''
        stroke = self.stroke.to_sexpr(indent+2) if self.stroke is not None else ''
        uuid = f' ( uuid "{dequote(self.uuid)}" )' if self.uuid is not None else ''
        layer =  f' (layer "{dequote(self.layer)}")' if self.layer is not None else ''
        angle = f' (angle {self.angle}' if self.angle is not None else ''
        width = f' (width {self.width})' if self.width is not None else  ''

        return f'{indents}(gr_line (start {self.start.X} {self.start.Y}) (end {self.end.X} {self.end.Y}){angle}{locked}{stroke}{layer}{width}{uuid}){endline}'

@dataclass
class GrRect():
    """The ``gr_rect`` token defines a graphical rectangle.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_rectangle
    """

    start: Position = field(default_factory=lambda: Position())
    """The ``start`` token defines the coordinates of the upper left corner of the rectangle"""

    end: Position = field(default_factory=lambda: Position())
    """The ``end`` token defines the coordinates of the low right corner of the rectangle"""

    layer: Optional[str] = None
    """The ``layer`` token defines the canonical layer the rectangle resides on"""

    width: Optional[float] = None     # Used for KiCad < 7
    """The ``width`` token defines the line width of the rectangle. (prior to version 7)"""

    fill: Optional[str] = None
    """The optional ``fill`` toke defines how the rectangle is filled. Valid fill types are solid and none. If not defined, the rectangle is not filled"""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    locked: bool = False
    """The ``locked`` token defines if the object may be moved or not"""

    stroke: Optional[Stroke] = None
    """The optional ``stroke`` token describes the style of an optional border to be drawn around 
    the text box"""

    @classmethod
    def from_sexpr(cls, exp: list) -> GrRect:
        """Convert the given S-Expresstion into a GrRect object

        Args:
            - exp (list): Part of parsed S-Expression ``(gr_rect ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not gr_rect

        Returns:
            - GrRect: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'gr_rect':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            if item[0] == 'start': object.start = Position.from_sexpr(item)
            if item[0] == 'end': object.end = Position.from_sexpr(item)
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'fill': object.fill = item[1]
            if item[0] == 'width': object.width = item[1]
            if item[0] == 'stroke': object.stroke = Stroke().from_sexpr(item)
        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        locked = f' ( locked yes )' if self.locked else ''
        stroke = self.stroke.to_sexpr(indent+2) if self.stroke is not None else ''
        uuid = f' ( uuid "{dequote(self.uuid)}" )' if self.uuid is not None else ''
        layer =  f' (layer "{dequote(self.layer)}")' if self.layer is not None else ''
        fill = f' (fill {self.fill})' if self.fill is not None else ''
        width = f' (width {self.width})' if self.width is not None else ''

        return f'{indents}(gr_rect (start {self.start.X} {self.start.Y}) (end {self.end.X} {self.end.Y}){locked}{stroke}{fill}{layer}{width}{uuid}){endline}'

@dataclass
class GrCircle():
    """The ``gr_circle `` token defines a graphical circle.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_circle
    """

    center: Position = field(default_factory=lambda: Position())
    """The ``center`` token defines the coordinates of the center of the circle"""

    end: Position = field(default_factory=lambda: Position())
    """The ``end`` token defines the coordinates of the low right corner of the circle"""

    layer: Optional[str] = None
    """The ``layer`` token defines the canonical layer the circle resides on"""

    width: Optional[float] = None # Used for KiCad < 7
    """The ``width`` token defines the line width of the circle. (prior to version 7)"""

    fill: Optional[str] = None
    """The optional ``fill`` toke defines how the circle is filled. Valid fill types are solid and none. If not defined, the rectangle is not filled"""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    locked: bool = False
    """The ``locked`` token defines if the object may be moved or not"""

    stroke: Optional[Stroke] = None
    """The optional ``stroke`` token describes the style of an optional border to be drawn around 
    the text box"""

    @classmethod
    def from_sexpr(cls, exp: list) -> GrCircle:
        """Convert the given S-Expresstion into a GrCircle object

        Args:
            - exp (list): Part of parsed S-Expression ``(gr_circle ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not gr_circle

        Returns:
            - GrCircle: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'gr_circle':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            if item[0] == 'center': object.center = Position.from_sexpr(item)
            if item[0] == 'end': object.end = Position.from_sexpr(item)
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'fill': object.fill = item[1]
            if item[0] == 'width': object.width = item[1]
            if item[0] == 'stroke': object.stroke = Stroke().from_sexpr(item)

        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        locked = f' ( locked yes )' if self.locked else ''

        uuid = f' ( uuid "{dequote(self.uuid)}" )' if self.uuid is not None else ''
        layer =  f' (layer "{dequote(self.layer)}")' if self.layer is not None else ''
        fill = f' (fill {self.fill})' if self.fill is not None else ''
        stroke = self.stroke.to_sexpr(indent+2) if self.stroke is not None else ''
        width = f' (width {self.width})' if self.width is not None else '' 

        return f'{indents}(gr_circle (center {self.center.X} {self.center.Y}) (end {self.end.X} {self.end.Y}){locked}{stroke}{fill}{layer}{width}{uuid}){endline}'

@dataclass
class GrArc():
    """The ``gr_arc`` token defines a graphic arc.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_arc
    """

    start: Position = field(default_factory=lambda: Position())
    """The ``start`` token defines the coordinates of the start position of the arc radius"""

    mid: Position = field(default_factory=lambda: Position())
    """The ``mid`` token defines the coordinates of the midpoint along the arc"""

    end: Position = field(default_factory=lambda: Position())
    """The ``end`` token defines the coordinates of the end position of the arc radius"""

    layer: Optional[str] = None
    """The ``layer`` token defines the canonical layer the arc resides on"""

    width: Optional[float] = None     # Used for KiCad < 7
    """The ``width`` token defines the line width of the arc. (prior to version 7)"""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    locked: bool = False
    """The ``locked`` token defines if the object may be moved or not"""

    stroke: Optional[Stroke] = None
    """The optional ``stroke`` token describes the style of an optional border to be drawn around 
    the text box"""


    @classmethod
    def from_sexpr(cls, exp: list) -> GrArc:
        """Convert the given S-Expresstion into a GrArc object

        Args:
            - exp (list): Part of parsed S-Expression ``(gr_arc ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not gr_arc

        Returns:
            - GrArc: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'gr_arc':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            if item[0] == 'start': object.start = Position.from_sexpr(item)
            if item[0] == 'mid': object.mid = Position.from_sexpr(item)
            if item[0] == 'end': object.end = Position.from_sexpr(item)
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'width': object.width = item[1]
            if item[0] == 'stroke': object.stroke = Stroke().from_sexpr(item)

        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        locked = f' ( locked yes )' if self.locked else ''
        stroke = self.stroke.to_sexpr(indent+2) if self.stroke is not None else ''
        uuid = f' ( uuid "{dequote(self.uuid)}" )' if self.uuid is not None else ''
        layer =  f' (layer "{dequote(self.layer)}")' if self.layer is not None else ''
        width = f' (width {self.width})' if self.width is not None else ''

        return f'{indents}(gr_arc (start {self.start.X} {self.start.Y}) (mid {self.mid.X} {self.mid.Y}) (end {self.end.X} {self.end.Y}){width}{locked}{stroke}{layer}{uuid}){endline}'

@dataclass
class GrPoly():
    """The ``gr_poly`` token defines a graphic polygon in a footprint definition.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_polygon
    """

    layer: Optional[str] = None
    """The ``coordinates`` define the list of X/Y coordinates of the polygon outline"""

    coordinates: List[Position] = field(default_factory=list)
    """The ``layer`` token defines the canonical layer the polygon resides on"""

    width: Optional[float] = None     # Used for KiCad < 7
    """The ``width`` token defines the line width of the polygon. (prior to version 7)"""

    fill: Optional[str] = None
    """The optional ``fill`` toke defines how the polygon is filled. Valid fill types are solid and none. If not defined, the rectangle is not filled"""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    locked: bool = False
    """The ``locked`` token defines if the object may be moved or not"""

    stroke: Optional[Stroke] = None
    """The optional ``stroke`` token describes the style of an optional border to be drawn around 
    the text box"""

    @classmethod
    def from_sexpr(cls, exp: list) -> GrPoly:
        """Convert the given S-Expresstion into a GrPoly object

        Args:
            - exp (list): Part of parsed S-Expression ``(gr_poly ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not gr_poly

        Returns:
            - GrPoly: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'gr_poly':
            raise Exception("Expression does not have the correct type")

        object = cls()

        for item in exp:
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            if item[0] == 'pts':
                for point in item[1:]:
                    object.coordinates.append(Position().from_sexpr(point))
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'fill': object.fill = item[1]
            if item[0] == 'width': object.width = item[1]
            if item[0] == 'stroke': object.stroke = Stroke.from_sexpr(item)

        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True, pts_newline: bool = False) -> str:
        """Generate the S-Expression representing this object. When no coordinates are set
        in the polygon, the resulting S-Expression will be left empty.

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.
            - pts_newline (bool): Adds a newline for the ``(pts ..)`` token as KiCad treats
                                  this different in Board files than Footprint files. Defaults to 
                                  False.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        if len(self.coordinates) == 0:
            return f'{indents}{endline}'

        uuid = f' ( uuid "{dequote(self.uuid)}" )' if self.uuid is not None else ''
        layer =  f' (layer "{dequote(self.layer)}")' if self.layer is not None else ''
        fill = f' (fill {self.fill})' if self.fill is not None else ''
        locked = f'( locked yes )' if self.locked else ''

        if pts_newline:
            expression =  f'{indents}(gr_poly\n'
            expression += f'{indents}  (pts\n'
        else:
            expression =  f'{indents}(gr_poly{locked} (pts\n'

        for point in self.coordinates:
            expression += sexpr.maybe_to_sexpr([point.X, point.Y], "xy", indent+4, True)
        expression += f'{indents}  ){endline}{endline}'
        if self.stroke is None:
            expression += f'{indents} {locked} {layer} (width {self.width}){fill}{uuid}){endline}'
        else:
            expression += f'{indents}{self.stroke.to_sexpr(indent, newline=False)}{fill}{layer}{uuid}){endline}'
        return expression

@dataclass
class GrCurve(SexprAuto):
    """The ``gr_curve`` token defines a graphic Cubic Bezier curve in a footprint definition.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_curve
    """
    sexpr_prefix: ClassVar[str] = "gr_curve"

    locked: Optional[bool] = None
    """The ``locked`` token defines if the object may be moved or not"""

    pts: List[Coordinate2D] = field(default_factory=list)
    """The ``pts`` define the list of X/Y coordinates of the curve outline"""

    width: Optional[float] = None     # Used for KiCad < 7
    """The ``width`` token defines the line width of the curve. (prior to version 7)"""

    stroke: Optional[Stroke] = None
    """The optional ``stroke`` token describes the style of line"""

    layer: Optional[str] = None
    """The ``layer`` token defines the canonical layer the curve resides on"""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    @property
    def coordinates(self) -> List[Position]:
        """Same as ``pts``"""
        return [cast(Position, i) for i in self.pts]

