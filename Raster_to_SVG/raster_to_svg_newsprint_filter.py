"""Copyright (c) 2017 abhishek-sehgal954
    
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
    """
import os
import sys
import base64

# Python 2
# import StringIO
# from urllib import url2pathname
# from urlparse import urlparse

# Python 3
from io import BytesIO
from urllib.request import url2pathname
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageStat

import inkex
from lxml import etree

try:
    inkex.localization.localize()
except:
    import gettext
    _ = gettext.gettext

try:
    from PIL import Image
except:
    inkex.errormsg(_(
        "The python module PIL is required for this extension.\n\n" +
        "Technical details:\n%s" % (e,)))
    sys.exit()


class raster_to_svg_newsprint_filter(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        

    def getImagePath(self, node, xlink):
        
        absref = node.get(inkex.addNS('absref', 'sodipodi'))
        url = urlparse(xlink)
        href = url2pathname(url.path)

        path = ''
       
        if href is not None:
            path = os.path.realpath(href)
        if (not os.path.isfile(path)):
            if absref is not None:
                path = absref

        try:
            path = unicode(path, "utf-8")
        except TypeError:
            path = path

        if (not os.path.isfile(path)):
            inkex.errormsg(_(
                "No xlink:href or sodipodi:absref attributes found, " +
                "or they do not point to an existing file! Unable to find image file."))
            if path:
                inkex.errormsg(_("Sorry we could not locate %s") % str(path))
            return False

        if (os.path.isfile(path)):
            return path

    def getImageData(self, xlink):
        """
        Read, decode and return data of embedded image
        """
        comma = xlink.find(',')
        data = ''

        if comma > 0:
            data = base64.decodebytes(xlink[comma:].encode())
        else:
            inkex.errormsg(_("Failed to read embedded image data."))

        return data

    def getImage(self, node):
        """
        Parse link attribute of node and retrieve image data
        """
        xlink = node.get(inkex.addNS('href', 'xlink'))
        image = ''

        if xlink is None or xlink[:5] != 'data:':
            # linked bitmap image
            path = self.getImagePath(node, xlink)
            if path:
                image = Image.open(path)
        elif xlink[:4] == 'data':
            # embedded bitmap image
            data = self.getImageData(xlink)
            if data:
                image = Image.open(BytesIO(data))
        else:
            # unsupported type of link detected
            inkex.errormsg(_("Unsupported type of 'xlink:href'"))

        return image


    def draw_rectangle(self, position, dimension, color, parent, id_):
        x, y = position
        l, b = dimension
        
        style = {'stroke': 'none', 'stroke-width': '1', 'fill': color,"mix-blend-mode" : "multiply"}
        attribs = {'style': str(inkex.Style(style)), 'x': str(x), 'y': str(y), 'width': str(l), 'height':str(b)}
        if id_ is not None:
            attribs.update({'id': id_})
        obj = etree.SubElement(parent, inkex.addNS('rect', 'svg'), attribs)
        return obj

    def draw_circle(self, position, r, color, parent, id_):
        x, y = position
        
        style = {'stroke': 'none', 'stroke-width': '1', 'fill': color,"mix-blend-mode" : "multiply"}
        attribs = {'style': str(inkex.Style(style)), 'cx': str(x), 'cy': str(y), 'r': str(r)}
        if id_ is not None:
            attribs.update({'id': id_})
        obj = etree.SubElement(parent, inkex.addNS('circle', 'svg'), attribs)
        return obj

    def draw_ellipse(self, position, radius, color, parent, id_,transform):
        x, y = position
        r1, r2 = radius
        
        style = {'stroke': 'none', 'stroke-width': '1', 'fill': color,"mix-blend-mode" : "multiply"}
        if(transform == 1.5):
            attribs = {'style': str(inkex.Style(style)), 'cx': str(x), 'cy': str(y), 'rx': str(r1), 'ry': str(r2),'transform': 'rotate(1.5)'}
        elif(transform == 3):
            attribs = {'style': str(inkex.Style(style)), 'cx': str(x), 'cy': str(y), 'rx': str(r1), 'ry': str(r2),'transform': 'rotate(3)'}
        else:
            attribs = {'style': str(inkex.Style(style)), 'cx': str(x), 'cy': str(y), 'rx': str(r1), 'ry': str(r2),'transform': 'rotate(0)'}

        if id_ is not None:
            attribs.update({'id': id_})
        obj = etree.SubElement(parent, inkex.addNS('ellipse', 'svg'), attribs)
        return obj

    def gcr(self,im, percentage):
        cmyk_im = im.convert('CMYK')
        if not percentage:
            return cmyk_im
        cmyk_im = cmyk_im.split()
        cmyk = []
        for i in range(4):
            cmyk.append(cmyk_im[i].load())
        for x in range(im.size[0]):
            for y in range(im.size[1]):
                gray = min(cmyk[0][x,y], cmyk[1][x,y], cmyk[2][x,y]) * percentage / 100
                for i in range(3):
                    cmyk[i][x,y] = cmyk[i][x,y] - gray
                cmyk[3][x,y] = gray
        return Image.merge('CMYK', cmyk_im)

    def halftone(self,parent,im, cmyk, sample, scale,):
        dots = []
        angle = 0 
        count = 0
        cmyk = cmyk.split()
        for channel in cmyk:
            count=count+1
            size = channel.size[0]*scale, channel.size[1]*scale
            for x in range(0, channel.size[0], sample):
                for y in range(0, channel.size[1], sample):
                    box = channel.crop((x, y, x + sample, y + sample))
                    stat = ImageStat.Stat(box)
                    diameter = (stat.mean[0] / 255)**0.5
                    edge = 0.5*(1-diameter)
                    x_pos, y_pos = (x+edge)*scale, (y+edge)*scale
                    box_edge = sample*diameter*scale
                    if(count==1):
                        self.draw_ellipse(((2*x_pos+box_edge)/2,(2*y_pos+box_edge)/2),(box_edge-5,box_edge-5),'cyan',parent,'id',0)
                      
                    elif(count==2):
                        self.draw_ellipse(((2*x_pos+box_edge)/2,(2*y_pos+box_edge)/2),(box_edge-5,box_edge-5),'magenta',parent,'id',1.5)
    
                    elif(count==3):
                        self.draw_ellipse(((2*x_pos+box_edge)/2,(2*y_pos+box_edge)/2),(box_edge-5,box_edge-5),'yellow',parent,'id',3)


    def clustered(self, node):
       
        image = self.getImage(node)
        if image:
            (width, height) = image.size
            nodeParent = node.getparent()
            nodeIndex = nodeParent.index(node)
            pixel2svg_group = etree.Element(inkex.addNS('g', 'svg'))
            pixel2svg_group.set('id', "%s_pixel2svg" % node.get('id'))
            nodeParent.insert(nodeIndex+1, pixel2svg_group)
            self.draw_rectangle((0,0),(width,height),'white',pixel2svg_group,'id')
            cmyk = self.gcr(image,0)
            self.halftone(pixel2svg_group,image,cmyk,10,1)
            nodeParent.remove(node)
        else:
            inkex.errormsg(_("Bailing out: No supported image file or data found"))
            sys.exit(1)

    def effect(self):
        found_image = False
        if (self.options.ids):
            for node in self.svg.selected.values():
                if node.tag == inkex.addNS('image', 'svg'):
                    found_image = True
                    self.clustered(node)

        if not found_image:
            inkex.errormsg(_("Please select one or more bitmap image(s)"))
            sys.exit(0)
        


if __name__ == '__main__':
    e = raster_to_svg_newsprint_filter()
    e.run()
