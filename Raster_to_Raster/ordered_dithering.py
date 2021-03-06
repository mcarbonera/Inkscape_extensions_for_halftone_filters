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
import numpy
from PIL import Image, ImageDraw, ImageStat
import inkex
import os
import common

def intensity(arr):
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

def order_dither(image):
  arr = numpy.asarray(image)
  brr = intensity(arr)
  crr = [[8, 3, 4], [6, 1, 2], [7, 5, 9]]
  drr = numpy.zeros((len(arr),len(arr[0])))
  for i in range(len(arr)):
    for j in range(len(arr[0])):
      if(brr[i][j] > crr[i%3][j%3]):
        drr[i][j] = 255
      else:
        drr[i][j] = 0
  return drr



class ordered_dithering(inkex.Effect):
	def __init__(self):
		inkex.Effect.__init__(self)
	def effect(self):
		image_node = None
		for node in self.svg.selected.values():
			if(common.is_image(node)):
				image_node = node
			if image_node is not None:
				image = common.prep_image(image_node)
				image = image.convert('L')
				data = order_dither(image)
				image = Image.fromarray(data)
				image = image.convert('RGB')
				common.save_image(image_node, image, img_format='PNG')

if __name__ == '__main__':
	obj = ordered_dithering()
	obj.run()

			
