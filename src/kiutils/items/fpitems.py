"""Footprint graphical items define all of the drawing items that are used in the footprint
definition. This includes text, text boxes, lines, rectangles, circles, arcs, polygons, curves
and dimensions.

Author:
    (C) Marvin Mager - @mvnmgrx - 2022

License identifier:
    GPL-3.0

Major changes:
    08.02.2022 - created

Documentation taken from:
    https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_footprint_graphics_items
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List

from kiutils.items.common import RenderCache, Stroke, Position, Effects
from kiutils.utils.strings import dequote
from kiutils.utils import sexpr

# FIXME: Several classes have a ``stroke`` member. This feature will be introduced in KiCad 7 and
#        has yet to be tested here.

@dataclass
class FpText():
    """The ``fp_text`` token defines a graphic line in a footprint definition.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_footprint_text
    """

    type: str = "reference"
    """The ``type`` attribute defines the type of text. Valid types are ``reference``, ``value``, and
    ``user``"""

    text: str = "%REF"
    """The ``text`` attribute is a string that defines the text"""

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` defines the X and Y position coordinates and optional orientation angle of
    the text"""

    layer: str = "F.Cu"
    """The ``layer`` token defines the canonical layer the text resides on"""

    knockout: bool = False
    """The ``knockout`` token defines if the text is inverted (means transparent text and colored
    background insted of colored text and transparent background)"""

    hide: bool = False
    """The optional ``hide`` token, defines if the text is hidden"""

    effects: Effects = field(default_factory=lambda: Effects())
    """The ``effects`` token defines how the text is displayed"""

    uuid: Optional[str] = None     
    """The optional ``uuid`` defines the universally unique identifier"""

    renderCache: Optional[RenderCache] = None
    """If the ``effects`` token prescribe a TrueType font then the optional ``render_cache`` token 
    should be given in case the font can not be found on the current system.
    
    Available since KiCad v7"""

    unlocked: Optional[bool] = None
    """The optional ``unlocked`` token defines if the object can be edited"""

    @classmethod
    def from_sexpr(cls, exp: list) -> FpText:
        """Convert the given S-Expresstion into a FpText object

        Args:
            - exp (list): Part of parsed S-Expression ``(fp_text ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not fp_text

        Returns:
            - FpText: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'fp_text':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.type = exp[1]
        object.text = exp[2]
        for item in exp[3:]:
            if item[0] == 'hide': object.hide = sexpr.parse_bool(item)
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'layer': 
                object.layer = item[1]
                if(len(item) > 2):
                    if(item[2] == "knockout"):
                        object.knockout = True
            if item[0] == 'effects': object.effects = Effects().from_sexpr(item)
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'render_cache': object.renderCache = RenderCache.from_sexpr(item)
            if item[0] == 'unlocked': object.unlocked = sexpr.parse_bool(item)
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

        hide = ' ( hide yes )' if self.hide else ''
        unlocked = ''
        if self.unlocked is not None:
            unlocked = ' (unlocked yes)' if self.unlocked else ' (unlocked no)'
        posA = f' {self.position.angle}' if self.position.angle is not None else ''
        ko = ' knockout' if self.knockout else ''

        expression =  f'{indents}(fp_text {self.type} "{dequote(self.text)}" (at {self.position.X} {self.position.Y}{posA}){unlocked} (layer "{dequote(self.layer)}"{ko}){hide}\n'
        if self.uuid is not None:
            expression += f'{indents}  (uuid "{dequote(self.uuid)}")\n'
        expression += f'{indents}  {self.effects.to_sexpr()}'
        if self.renderCache is not None:
            expression += self.renderCache.to_sexpr(indent+2)
        expression += f'{indents}){endline}'
        return expression

@dataclass
class FpLine():
    """The ``fp_line`` token defines a graphic line in a footprint definition.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_footprint_line
    """

    start: Position = field(default_factory=lambda: Position())
    """The ``start`` token defines the coordinates of the upper left corner of the line"""

    end: Position = field(default_factory=lambda: Position())
    """The ``end`` token defines the coordinates of the low right corner of the line"""

    layer: str = "F.Cu"
    """The ``layer`` token defines the canonical layer the line resides on"""

    width: Optional[float] = 0.12     # Used for KiCad < 7
    """The ``width`` token defines the line width of the line. (prior to version 7)"""

    stroke: Optional[Stroke] = None   # Used for KiCad >= 7
    """The ``stroke`` describes the line width and style of the line. (version 7)"""

    # FIXME: This is not implemented in to_sexpr() because it does not seem to be used on lines
    #        in footprints. Further testing required ..
    locked: bool = False
    """The optional ``locked`` token defines if the line cannot be edited"""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> FpLine:
        """Convert the given S-Expresstion into a FpLine object

        Args:
            - exp (list): Part of parsed S-Expression ``(fp_line ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not fp_line

        Returns:
            - FpLine: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'fp_line':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            if item[0] == 'start': object.start = Position.from_sexpr(item)
            if item[0] == 'end': object.end = Position.from_sexpr(item)
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'width':
                object.width = item[1]
                object.stroke = None
            if item[0] == 'stroke':
                object.stroke = Stroke.from_sexpr(item)
                object.width = None

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
        uuid = f' ( uuid "{dequote(self.uuid)}" )' if self.uuid is not None else ''
        locked = f'( locked yes )' if self.locked else ''
        if self.width is not None:
            width = f' (width {self.width})'
        elif self.stroke is not None:
            width = f' {self.stroke.to_sexpr(indent=0, newline=False)}'
        else:
            width = ''

        return f'{indents}(fp_line (start {self.start.X} {self.start.Y}) (end {self.end.X} {self.end.Y}){width}{locked} (layer "{dequote(self.layer)}"){uuid}){endline}'

@dataclass
class FpRect():
    """The ``fp_rect`` token defines a graphic rectangle in a footprint definition.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_footprint_rectangle
    """

    start: Position = field(default_factory=lambda: Position())
    """The ``start`` token defines the coordinates of the upper left corner of the rectangle"""

    end: Position = field(default_factory=lambda: Position())
    """The ``end`` token defines the coordinates of the low right corner of the rectangle"""

    layer: str = "F.Cu"
    """The ``layer`` token defines the canonical layer the rectangle resides on"""

    width: Optional[float] = 0.12     # Used for KiCad < 7
    """The ``width`` token defines the line width of the rectangle. (prior to version 7)"""

    stroke: Optional[Stroke] = None   # Used for KiCad >= 7
    """The ``stroke`` describes the line width and style of the rectangle. (version 7)"""

    fill: Optional[str] = None
    """The optional ``fill`` toke defines how the rectangle is filled. Valid fill types are solid
    and none. If not defined, the rectangle is not filled."""

    locked: bool = False
    """The optional ``locked`` token defines if the rectangle cannot be edited"""

    uuid: Optional[str] = None 
    """The optional ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> FpRect:
        """Convert the given S-Expresstion into a FpRect object

        Args:
            - exp (list): Part of parsed S-Expression ``(fp_rect ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not fp_rect

        Returns:
            - FpRect: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'fp_rect':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            if item[0] == 'start': object.start = Position.from_sexpr(item)
            if item[0] == 'end': object.end = Position.from_sexpr(item)
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'fill': object.fill = item[1]
            if item[0] == 'width':
                object.width = item[1]
                object.stroke = None
            if item[0] == 'stroke':
                object.stroke = Stroke.from_sexpr(item)
                object.width = None

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

        uuid = f' ( uuid "{dequote(self.uuid)}" )' if self.uuid is not None else ''
        locked = ' (locked yes)' if self.locked else ''
        fill = f' (fill {self.fill})' if self.fill is not None else ''

        if self.width is not None:
            width = f' (width {self.width})'
        elif self.stroke is not None:
            width = f' {self.stroke.to_sexpr(indent=0, newline=False)}'
        else:
            width = ''

        return f'{indents}(fp_rect (start {self.start.X} {self.start.Y}) (end {self.end.X} {self.end.Y}){width}{fill}{locked} (layer "{dequote(self.layer)}"){uuid}){endline}'

@dataclass
class FpTextBox():
    """The ``fp_text_box`` token defines a rectangle containing line-wrapped text.
    
    Available since KiCad v7
    
    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_footprint_text_box
    """

    locked: bool = False
    """The ``locked`` token specifies if the text box can be moved. Defaults to ``False``."""

    text: str = ""
    """The ``text`` token defines the content of the text box. Defaults to an empty string."""

    start: Optional[Position] = None
    """The optional ``start`` token defines the top-left of a cardinally oriented text box"""

    end: Optional[Position] = None
    """The optional ``end`` token defines the bottom-right of a cardinally oriented text box"""

    pts: List[Position] = field(default_factory=list)
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

    stroke: Optional[Stroke] = None
    """The optional ``stroke`` token describes the style of an optional border to be drawn around 
    the text box"""

    renderCache: Optional[RenderCache] = None
    """If the ``effects`` token prescribe a TrueType font then the optional ``render_cache`` token 
    should be given in case the font can not be found on the current system."""

    @classmethod
    def from_sexpr(cls, exp: list) -> FpTextBox:
        """Convert the given S-Expression into a FpTextBox object

        Args:
            - exp (list): Part of parsed S-Expression ``(fp_text_box ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not fp_text_box

        Returns:
            - FpTextBox: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list) or len(exp) < 2:
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'fp_text_box':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.text=exp[1]

        for item in exp[2:]:
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            if item[0] == 'start': object.start = Position.from_sexpr(item)
            if item[0] == 'end': object.end = Position.from_sexpr(item)
            if item[0] == 'pts':
                for point in item[1:]:
                    object.pts.append(Position().from_sexpr(point))
            if item[0] == 'angle': object.angle = item[1]
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'effects': object.effects = Effects.from_sexpr(item)
            if item[0] == 'stroke': object.stroke = Stroke.from_sexpr(item)
            if item[0] == 'render_cache': object.renderCache = RenderCache.from_sexpr(item)
            
        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Raises:
            - Exception: When a non-cardinal angle is given and no corner points were defined using
              the ``self.pts`` token
            - Exception: When a cardinal angle or no angle is given and either start or end token
              is undefined

        Returns:
            - str: S-Expression of this object
        """
        if self.angle is not None and self.angle not in [0.0, 90.0, 180.0, 270.0]:
            if len(self.pts) != 4:
                raise Exception("None-cardinal angles must have exactly four corner points defined")
        if self.angle is None or self.angle in [0.0, 90.0, 180.0, 270.0]:
            if self.start is None or self.end is None:
                raise Exception("No angle or a cardinal angle needs a start and end token defined")

        indents = ' '*indent
        endline = '\n' if newline else ''

        uuid = f' ( uuid "{dequote(self.uuid)}" )' if self.uuid is not None else ''
        angle = f'(angle {self.angle}) ' if self.angle is not None else ''
        start = f'(start {self.start.X} {self.start.Y}) ' if self.start is not None else ''
        end = f'(end {self.end.X} {self.end.Y}) ' if self.end is not None else ''
        locked = ' (locked yes)' if self.locked else ''

        expression = f'{indents}(fp_text_box "{dequote(self.text)}"\n'
        if len(self.pts) == 4:
            expression += f'{indents}  (pts\n'
            expression += f'{indents}    (xy {self.pts[0].X} {self.pts[0].Y})      (xy {self.pts[1].X} {self.pts[1].Y})      (xy {self.pts[2].X} {self.pts[2].Y})      (xy {self.pts[3].X} {self.pts[3].Y})\n'
            expression += f'{indents}  )\n'
        expression += f'{indents}  {start}{end}{angle}(layer "{dequote(self.layer)}"){locked}{uuid}\n'
        if self.effects is not None:
            expression += self.effects.to_sexpr(indent+2)
        if self.stroke is not None:
            expression += self.stroke.to_sexpr(indent+2)
        if self.renderCache is not None:
            expression += self.renderCache.to_sexpr(indent+2)
        expression += f'{indents}){endline}'
        return expression

@dataclass
class FpCircle():
    """The ``fp_circle `` token defines a graphic circle in a footprint definition.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_footprint_circle
    """

    center: Position = field(default_factory=lambda: Position())
    """The ``center`` token defines the coordinates of the center of the circle"""

    end: Position = field(default_factory=lambda: Position())
    """The ``end`` token defines the coordinates of the low right corner of the circle"""

    layer: str = "F.Cu"
    """The ``layer`` token defines the canonical layer the circle resides on"""

    width: Optional[float] = 0.12     # Used for KiCad < 7
    """The ``width`` token defines the line width of the circle. (prior to version 7)"""

    stroke: Optional[Stroke] = None   # Used for KiCad >= 7
    """The ``stroke`` describes the line width and style of the circle. (version 7)"""

    fill: Optional[str] = None
    """The optional ``fill`` toke defines how the circle is filled. Valid fill types are ``solid``
    and ``none``. If not defined, the circle is not filled."""

    locked: bool = False
    """The optional ``locked`` token defines if the circle cannot be edited"""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> FpCircle:
        """Convert the given S-Expresstion into a FpCircle object

        Args:
            - exp (list): Part of parsed S-Expression ``(fp_circle ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not fp_circle

        Returns:
            - FpCircle: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'fp_circle':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            if item[0] == 'center': object.center = Position.from_sexpr(item)
            if item[0] == 'end': object.end = Position.from_sexpr(item)
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'fill': object.fill = item[1]
            if item[0] == 'width':
                object.width = item[1]
                object.stroke = None
            if item[0] == 'stroke':
                object.stroke = Stroke.from_sexpr(item)
                object.width = None

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

        uuid = f' ( uuid "{dequote(self.uuid)}" )' if self.uuid is not None else ''
        locked = ' (locked yes)' if self.locked else ''
        fill = f' (fill {self.fill})' if self.fill is not None else ''

        if self.width is not None:
            width = f' (width {self.width})'
        elif self.stroke is not None:
            width = f' {self.stroke.to_sexpr(indent=0, newline=False)}'
        else:
            width = ''

        return f'{indents}(fp_circle (center {self.center.X} {self.center.Y}) (end {self.end.X} {self.end.Y}){width}{fill}{locked} (layer "{dequote(self.layer)}"){uuid}){endline}'

@dataclass
class FpArc():
    """The ``fp_arc`` token defines a graphic arc in a footprint definition.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_footprint_arc
    """

    start: Position = field(default_factory=lambda: Position())
    """The ``start`` token defines the coordinates of the start position of the arc radius"""

    mid: Position = field(default_factory=lambda: Position())
    """The ``mid`` token defines the coordinates of the midpoint along the arc"""

    end: Position = field(default_factory=lambda: Position())
    """The ``end`` token defines the coordinates of the end position of the arc radius"""

    layer: str = "F.Cu"
    """The ``layer`` token defines the canonical layer the arc resides on"""

    width: Optional[float] = 0.12     # Used for KiCad < 7
    """The ``width`` token defines the line width of the arc. (prior to version 7)"""

    stroke: Optional[Stroke] = None   # Used for KiCad >= 7
    """The ``stroke`` describes the line width and style of the arc. (version 7)"""

    locked: bool = False
    """The optional ``locked`` token defines if the arc cannot be edited"""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> FpArc:
        """Convert the given S-Expresstion into a FpArc object

        Args:
            - exp (list): Part of parsed S-Expression ``(fp_arc ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not fp_arc

        Returns:
            - FpArc: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'fp_arc':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            if item[0] == 'start': object.start = Position.from_sexpr(item)
            if item[0] == 'mid': object.mid = Position.from_sexpr(item)
            if item[0] == 'end': object.end = Position.from_sexpr(item)
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'width':
                object.width = item[1]
                object.stroke = None
            if item[0] == 'stroke':
                object.stroke = Stroke.from_sexpr(item)
                object.width = None

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

        uuid = f' ( uuid "{dequote(self.uuid)}" )' if self.uuid is not None else ''
        locked = ' (locked yes)' if self.locked else ''

        if self.width is not None:
            width = f' (width {self.width})'
        elif self.stroke is not None:
            width = f' {self.stroke.to_sexpr(indent=0, newline=False)}'
        else:
            width = ''

        return f'{indents}(fp_arc (start {self.start.X} {self.start.Y}) (mid {self.mid.X} {self.mid.Y}) (end {self.end.X} {self.end.Y}){width}{locked} (layer "{dequote(self.layer)}"){uuid}){endline}'

@dataclass
class FpPoly():
    """The ``fp_poly`` token defines a graphic polygon in a footprint definition.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_footprint_polygon
    """

    layer: str = "F.Cu"
    """The ``layer`` token defines the canonical layer the polygon resides on"""

    coordinates: List[Position] = field(default_factory=list)
    """The ``coordinates`` define the list of X/Y coordinates of the polygon outline"""

    width: Optional[float] = 0.12     # Used for KiCad < 7
    """The ``width`` token defines the line width of the polygon. (prior to version 7)"""

    stroke: Optional[Stroke] = None   # Used for KiCad >= 7
    """The ``stroke`` describes the line width and style of the polygon. (version 7)"""

    fill: Optional[str] = None
    """The optional ``fill`` toke defines how the polygon is filled. Valid fill types are solid
    and none. If not defined, the rectangle is not filled."""

    locked: bool = False
    """The optional ``locked`` token defines if the polygon cannot be edited"""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> FpPoly:
        """Convert the given S-Expresstion into a FpPoly object

        Args:
            - exp (list): Part of parsed S-Expression ``(fp_poly ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not fp_poly

        Returns:
            - FpPoly: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'fp_poly':
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
            if item[0] == 'width':
                object.width = item[1]
                object.stroke = None
            if item[0] == 'stroke':
                object.stroke = Stroke.from_sexpr(item)
                object.width = None

        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True) -> str:
        """Generate the S-Expression representing this object. When no coordinates are set
        in the polygon, the resulting S-Expression will be left empty.

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        if len(self.coordinates) == 0:
            return f'{indents}{endline}'

        uuid = f' ( uuid "{dequote(self.uuid)}" )' if self.uuid is not None else ''
        locked = ' (locked yes)' if self.locked else ''
        fill = f' (fill {self.fill})' if self.fill is not None else ''

        if self.width is not None:
            width = f' (width {self.width})'
        elif self.stroke is not None:
            width = f' {self.stroke.to_sexpr(indent=0, newline=False)}'
        else:
            width = ''

        expression = f'{indents}(fp_poly (pts\n'
        for point in self.coordinates:
            expression += f'{indents}    (xy {point.X} {point.Y})\n'
        expression += f'{indents}  ){width}{fill}{locked} (layer "{dequote(self.layer)}"){uuid}){endline}'
        return expression

@dataclass
class FpCurve():
    """The ``fp_curve`` token defines a graphic Cubic Bezier curve in a footprint definition.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_footprint_curve
    """

    coordinates: List[Position] = field(default_factory=list)
    """The ``coordinates`` define the list of X/Y coordinates of the curve outline"""

    layer: str = "F.Cu"
    """The ``layer`` token defines the canonical layer the curve resides on"""

    width: Optional[float] = 0.12     # Used for KiCad < 7
    """The ``width`` token defines the line width of the curve. (prior to version 7)"""

    stroke: Optional[Stroke] = None   # Used for KiCad >= 7
    """The ``stroke`` describes the line width and style of the curve. (version 7)"""

    locked: bool = False
    """The optional ``locked`` token defines if the curve cannot be edited"""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier""" 

    @classmethod
    def from_sexpr(cls, exp: list) -> FpCurve:
        """Convert the given S-Expresstion into a FpCurve object

        Args:
            - exp (list): Part of parsed S-Expression ``(fp_curve ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not fp_curve

        Returns:
            - FpCurve: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'fp_curve':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'locked': object.locked = sexpr.parse_bool(item)
            if item[0] == 'pts':
                for point in item[1:]:
                    object.coordinates.append(Position().from_sexpr(point))
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'width':
                object.width = item[1]
                object.stroke = None
            if item[0] == 'stroke':
                object.stroke = Stroke.from_sexpr(item)
                object.width = None

        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True) -> str:
        """Generate the S-Expression representing this object. When no coordinates are set
        in the curve, the resulting S-Expression will be left empty.

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        if len(self.coordinates) == 0:
            return f'{indents}{endline}'

        uuid = f' ( uuid "{dequote(self.uuid)}" )' if self.uuid is not None else ''
        locked = ' (locked yes)' if self.locked else ''

        if self.width is not None:
            width = f' (width {self.width})'
        elif self.stroke is not None:
            width = f' {self.stroke.to_sexpr(indent=0, newline=False)}'
        else:
            width = ''

        expression = f'{indents}(fp_curve (pts\n'
        for point in self.coordinates:
            expression += f'{indents}  (xy {point.X} {point.Y})\n'
        expression += f'{indents}){width}{locked} (layer "{dequote(self.layer)}"){uuid}){endline}'
        return expression


@dataclass
class FpProperty:
    """The ``property`` token defines a footprint property when used inside a ``footprint`` definition.

    This can store such information about footprint as Reference, Value, Datasheet, ..
    """

    key: str = ""
    """The ``key`` string defines the name of the property and must be unique"""

    value: str = ""
    """The ``value`` string defines the value of the property"""

    position: Optional[Position] = None
    """The ``position`` defines the X and Y position coordinates and optional orientation angle of
    the text"""

    layer: Optional[str] = None
    """The ``layer`` token defines the canonical layer the text resides on"""

    hide: Optional[bool] = None
    """The optional ``hide`` token, defines if the text is hidden"""

    effects: Optional[Effects] = None
    """The ``effects`` token defines how the text is displayed"""

    uuid: Optional[str] = None
    """The optional ``uuid`` defines the universally unique identifier"""

    unlocked: Optional[bool] = None
    """The optional ``unlocked`` token defines if the property can be edited"""

    @classmethod
    def from_sexpr(cls, exp: list) -> FpProperty:
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")
        if exp[0] != 'property':
            raise Exception("Expression does not have the correct type")
        object = cls()
        object.key = exp[1]
        object.value = exp[2]
        for item in exp[3:]:
            if item[0] == 'hide': object.hide = sexpr.parse_bool(item)
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'effects': object.effects = Effects().from_sexpr(item)
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'unlocked': object.unlocked = sexpr.parse_bool(item)
        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True) -> str:
        indents = " " * indent
        endline = "\n" if newline else ""

        if self.key in ["ki_fp_filters"]:
            key = self.key
        else:
            key = f'"{self.key}"'

        expression = f'{indents}(property {key}{sexpr.maybe_to_sexpr([self.value, self.position, (self.unlocked, "unlocked"), (self.layer, "layer"), (self.hide, "hide")])}\n'
        expression += sexpr.maybe_to_sexpr(self.uuid, "uuid", indent + 2, True)
        expression += sexpr.maybe_to_sexpr(self.effects, indent=indent + 2)
        expression += f"{indents}){endline}"
        return expression
