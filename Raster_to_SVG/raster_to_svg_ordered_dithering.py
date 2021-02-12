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
from io import BytesIO
from urllib.request import url2pathname
from urllib.parse import urlparse
from PIL import Image, ImageDraw, ImageStat
import numpy as np

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


class raster_to_svg_ordered_dithering(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)

        self.arg_parser.add_argument("-t", "--width",
                                     action="store", type=int,
                                     dest="width", default=200,
                                     help="this variable will be used to resize the original selected image to a width of whatever \
                                     you enter and height proportional to the new width, thus maintaining the aspect ratio")
        

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


    def draw_rectangle(self, position, dimensions, color, parent, id_):
        x, y = position
        l, b = dimensions
        
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

    def draw_ellipse(self, position, radius, color, parent, id_):
        x, y = position
        r1, r2 = radius
        
        style = {'stroke': 'none', 'stroke-width': '1', 'fill': color,"mix-blend-mode" : "multiply"}
        attribs = {'style': str(inkex.Style(style)), 'cx': str(x), 'cy': str(y), 'rx': str(r1), 'ry': str(r2)}
        if id_ is not None:
            attribs.update({'id': id_})
        obj = etree.SubElement(parent, inkex.addNS('ellipse', 'svg'), attribs)
        return obj

    
    def draw_svg(self,output,parent):
        startu = 0
        endu = 0
        for i in range(len(output)):
            for j in range(len(output[i])):
                if (output[i][j]==0):
                    self.draw_circle((int((startu+startu+1)/2),int((endu+endu+1)/2)),1,'black',parent,'id')
                    #dwg.add(dwg.circle((int((startu+startu+1)/2),int((endu+endu+1)/2)),1,fill='black'))        
                startu = startu+2                                                                               
            endu = endu+2
            startu = 0

  #dwg.save() 
    def intensity(self,arr):
  #  calcluates intensity of a pixel from 0 to 9
        mini = 999
        maxi = 0
        for i in range(len(arr)):
            for j in range(len(arr[0])):
                maxi = max(arr[i][j],maxi)
                mini = min(arr[i][j],mini)
        level = float(float(maxi-mini)/float(10));
        brr = [[0]*len(arr[0]) for i in range(len(arr))]
        for i in range(10):
            l1 = mini+level*i
            l2 = l1+level
            for j in range(len(arr)):
                for k in range(len(arr[0])):
                    if(arr[j][k] >= l1 and arr[j][k] <= l2):
                        brr[j][k]=i
        return brr

    def order_dither(self,image):
        arr = np.asarray(image)
        brr = self.intensity(arr)
        crr = [[8, 3, 4], [6, 1, 2], [7, 5, 9]]
        drr = np.zeros((len(arr),len(arr[0])))
        for i in range(len(arr)):
            for j in range(len(arr[0])):
                if(brr[i][j] > crr[i%3][j%3]):
                    drr[i][j] = 255
            else:
                drr[i][j] = 0
        return drr


    

    def dithering(self, node):
       
        image = self.getImage(node)
        image = image.convert('L')

        if image:
            basewidth = self.options.width
            wpercent = (basewidth/float(image.size[0]))
            hsize = int((float(image.size[1])*float(wpercent)))
            image = image.resize((basewidth,hsize), Image.ANTIALIAS)
            (width, height) = image.size
            nodeParent = node.getparent()
            nodeIndex = nodeParent.index(node)
            pixel2svg_group = etree.Element(inkex.addNS('g', 'svg'))
            pixel2svg_group.set('id', "%s_pixel2svg" % node.get('id'))
            nodeParent.insert(nodeIndex+1, pixel2svg_group)
            self.draw_rectangle((0,0),(basewidth,hsize),'white',pixel2svg_group,'id')
            output = self.order_dither(image)
            self.draw_svg(output,pixel2svg_group)
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
                    self.dithering(node)

        if not found_image:
            inkex.errormsg(_("Please select one or more bitmap image(s)"))
            sys.exit(0)
        


if __name__ =='__main__':
    e = raster_to_svg_ordered_dithering()
    e.run()
