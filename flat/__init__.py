# 
# Flat - Generative infrastructure for Python
# 
# https://xxyxyz.org/flat
# 
# Copyright (c) 2013-2020 Juraj Sukop
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to 
# deal in the Software without restriction, including without limitation the 
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or 
# sell copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL 
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS 
# IN THE SOFTWARE.
# 

__all__ = [
    'gray', 'ga', 'rgb', 'rgba', 'cmyk', 'spot', 'overprint',
    'moveto', 'lineto', 'quadto', 'curveto', 'closepath',
    'document',
    'view',
    'tree',
    'font',
    'group',
    'image', 'raw',
    'mesh',
    'union', 'intersection', 'difference',
    'diffuse', 'scene',
    'shape',
    'parsepath',
    'strike', 'paragraph', 'text', 'outlines']
__version__ = '0.3.2'

from .color import gray, ga, rgb, rgba, cmyk, spot, overprint
from .command import moveto, lineto, quadto, curveto, closepath
from .document import document
from .even import view
from .extra import tree
from .font import font
from .group import group
from .image import image, raw
from .mesh import mesh
from .path import union, intersection, difference
from .scene import diffuse, scene
from .shape import shape
from .svg import parsepath
from .text import strike, paragraph, text, outlines




