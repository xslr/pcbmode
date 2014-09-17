#!/usr/bin/python

import os
import re
import json
from lxml import etree as et

import config
import messages as msg

# pcbmode modules
import svg 
import utils
import place
from style import Style
from point import Point
from shape import Shape



class Footprint():
    """
    """

    def __init__(self, footprint):

        self._footprint = footprint

        self._shapes = {'copper': {'top': [], 'bottom': [], 'internal': []},
                        'soldermask': {'top': [], 'bottom': []},
                        'silkscreen': {'top': [], 'bottom': []},
                        'assembly': {'top': [], 'bottom': []},
                        'solderpaste': {'top': [], 'bottom': []},
                        'drills': {'top': [], 'bottom': [], 'internal': []},
                        'pin-labels': {'top': [], 'bottom': [], 'internal': []}}


        self._processPins()
        self._processSilkscreenShapes()
        self._processAssemblyShapes()




    def getShapes(self):
        return self._shapes



    def _processPins(self):
        """
        Converts pins into 'shapes'
        """

        try:
            pins = self._footprint['pins']
        except:
            msg.error("Cannot find any 'pins' specified!")


        for pin in pins:

            pin_location = pins[pin]['layout']['location'] or [0, 0]

            try:
                pad_name = pins[pin]['layout']['pad']
            except:
                msg.error("Each defined 'pin' must have a 'pad' name that is defined in the 'pads' dection of the footprint.")

            try:
                pad_dict = self._footprint['pads'][pad_name]
            except:
                msg.error("There doesn't seem to be a pad definition for pad '%s'." % pad_name)

            # Get the pin's rotation, if any
            pin_rotate = pins[pin]['layout'].get('rotate') or 0

            shapes = pad_dict.get('shapes') or []

            for shape_dict in shapes:

                shape_dict = shape_dict.copy()

                # Which layer(s) to place the shape on
                layers = shape_dict.get('layer') or ['top']

                # Add the pin's location to the pad's location
                shape_location = shape_dict.get('location') or [0, 0]
                shape_dict['location'] = [shape_location[0] + pin_location[0],
                                          shape_location[1] + pin_location[1]]

                
                # Add the pin's rotation to the pad's rotation
                shape_dict['rotate'] = (shape_dict.get('rotate') or 0) + pin_rotate

                # Determine if and which label to show
                show_name = pins[pin]['layout'].get('show-label') or True
                if show_name == True:
                    pin_label = pins[pin]['layout'].get('label')
                    if pin_label == None:
                        pin_label = pin
                pn_label = None

                # The same shape can go on multiple layers
                for layer in layers:
                    
                    shape = Shape(shape_dict)
                    style = Style(shape_dict, 'copper')
                    shape.setStyle(style)
                    try:
                        # This will capture of 'layer' is defined as a
                        # list rather than a string. Ther's bound to
                        # be a better way of doing this
                        self._shapes['copper'][layer].append(shape)
                    except:
                        msg.error("The same pad shape can be placed on multiple layers. Even if it is only placed on a single layer, the layer needs to be defined as an array, for example, 'layer':['top']")

                    # Soldermask shape, if any is specified
                    sm_dict = shape_dict.get('soldermask') 

                    if sm_dict == None:
                        sm_dict = shape_dict.copy()
                        sp_dict = shape_dict.copy()
                        sm_dict['scale'] = shape.getScale()*config.brd['soldermask']['scale']
                        sp_dict['scale'] = shape.getScale()*config.brd['solderpaste']['scale']
                        sm_shape = Shape(sm_dict)
                        sp_shape = Shape(sp_dict)
                        sm_style = Style(sm_dict, 'soldermask')
                        sp_style = Style(sp_dict, 'soldermask')
                        sm_shape.setStyle(sm_style)
                        sp_shape.setStyle(sp_style)
                        self._shapes['soldermask'][layer].append(sm_shape)
                        self._shapes['solderpaste'][layer].append(sp_shape)
                    elif sm_dict == {}:
                        # This indicates that we don't want any soldermask
                        # for this shape
                        pass
                    else:
                        # Soldermask is a shape definition of its own
                        sm_dict = sm_dict.copy()
                        sp_dict = sm_dict.copy()
                        shape_location = sm_dict.get('location') or [0, 0]
                        sm_dict['location'] = [shape_location[0] + pin_location[0],
                                               shape_location[1] + pin_location[1]]                        
                        sp_dict['location'] = [shape_location[0] + pin_location[0],
                                               shape_location[1] + pin_location[1]]                        
                        sm_shape = Shape(sm_dict)
                        sp_shape = Shape(sp_dict)
                        sm_style = Style(sm_dict, 'soldermask')
                        sp_style = Style(sp_dict, 'solderpaste')
                        sm_shape.setStyle(sm_style)
                        sp_shape.setStyle(sp_style)
                        self._shapes['soldermask'][layer].append(sm_shape)
                        self._shapes['solderpaste'][layer].append(sp_shape)

                    # Add pin label
                    if pin_label != None:
                        label = {}
                        label['text'] = pin_label
                        label['location'] = shape_dict['location']
                        self._shapes['pin-labels'][layer].append(label)





            drills = pad_dict.get('drills') or []
            for drill_dict in drills:
                drill_dict = drill_dict.copy()
                drill_dict['type'] = drill_dict.get('type') or 'drill'
                drill_location = drill_dict.get('location') or [0, 0]
                drill_dict['location'] = [drill_location[0] + pin_location[0],
                                          drill_location[1] + pin_location[1]]
                shape = Shape(drill_dict)
                style = Style(drill_dict, 'drills')
                shape.setStyle(style)
                self._shapes['drills']['top'].append(shape)                
                        






    def _processSilkscreenShapes(self):
        """
        """
        try:
            shapes = self._footprint['layout']['silkscreen']['shapes']
        except:
            return

        for shape_dict in shapes:
            layers = shape_dict.get('layer') or ['top']
            shape = Shape(shape_dict)
            style = Style(shape_dict, 'silkscreen')
            shape.setStyle(style)

            for layer in layers:
                self._shapes['silkscreen'][layer].append(shape)





    def _processAssemblyShapes(self):
        """
        """
        try:
            shapes = self._footprint['layout']['assembly']['shapes']
        except:
            return

        for shape_dict in shapes:
            layers = shape_dict.get('layer') or ['top']
            shape = Shape(shape_dict)
            style = Style(shape_dict, 'assembly')
            shape.setStyle(style)

            for layer in layers:
                self._shapes['assembly'][layer].append(shape)


