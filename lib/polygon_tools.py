#------------------------------------------------------------------------------
#  polygon_tools.py
#
#  By Shaun Astbury (shaast@ceh.ac.uk), Created: 18/07/14, Modified: 10/06/15
#------------------------------------------------------------------------------


"""
Python module created for the LUCI ArcGIS toolbox, derived from existing code
developed under the CEH Glastir Monitoring and Evaluation Programme (GMEP).

Contains tools to extract and modify polygon feature class extents, and
to generate grid feature classes from input extents.

Contents:
       
    1. extent (function): Extracts the extent of a feature class, and applies
       an optional buffer and/or rounds coordinates to specified significant
       figures.
           
    2. create_grid (function): Constructs a grid with square-shaped cells of
       equal size, which overlaps the extent of the input extent object.
          
"""

# Import required modules.
import arcpy
import math
import numpy as np

#------------------------------------------------------------------------------
#  1. extent (function): Extracts the extent of a feature class, and applies an
#     optional buffer and/or rounds coordinates to specified significant
#     figures.
#------------------------------------------------------------------------------

def extent(in_file, buffer_length=0, align=False, sig_figs=3):
    """
    Extracts, and optionally modifies, the extent of an input polygon feature
    class. Where appropriate, it is preferable to use the align and sig_fig
    options to round up the extent, to avoid the rounding error that often
    arises from floating point arithmetic (see
    https://docs.python.org/2/tutorial/floatingpoint.html). However, even if
    not aligning the extent, some minor rounding may still occur to attempt to
    eliminate this error so features are generated with the intended cell size.
    
    Arguments:

        in_file (file):
            An ArcGIS-readable feature class to have the extent extracted.

        buffer_length (float|int|long):
            An optional buffer to apply to the output coordinate extent
            (optional|default=0).

        align (bool):
            If True, sets the grid to integer extent values, and aligns to
            appropriate coordinates, rounding min xy values down, and max xy
            up, depending on the distance between the shortest polygon extent
            side (optional|default=False).
            
        sig_figs (int):
            Number of significant figures to align the coordinates to. This
            refers to the difference between the shortest length, so for
            coordinates of 123411 and 123511, where the difference is 100, and
            a sig_figs value of 2, the output would be 123410 and 123510.
            (optional|default=3).
            
    Returns:

        extent (tuple):
            An extent array for use as an input to create_grid.             

    """
        
    # Set initial extent from arcpy Describe object.
    desc = arcpy.Describe(in_file)
    min_x = desc.Extent.XMin
    min_y = desc.Extent.YMin
    max_x = desc.Extent.XMax
    max_y = desc.Extent.YMax
    coords = [min_x, min_y, max_x, max_y]
    
    # Crude method to identify coordinates containing erroneous float values,
    # determined as an integer followed by 3+ zeros e.g. 123.000 (floating
    # point error typically occurs at >3 decimal places). For example, if a
    # coord equals 123.000123, it is rounded to 123.000 and can be an integer.
    # If it was 123.0123, it would be rounded to 123.012, and should remain as
    # a float. If all coords are viable as integers, integerise the set.

    # if all(map(lambda coord: int(coord) == round(coord, 3), coords)): Old Python 2 code. The next line will hopefully work ok with both Python 2 and 3.
    if all([int(coord) == round(coord, 3) for coord in coords]): 
        coords = [int(coord) for coord in coords]

    else:
        
        # For true floating point coordinates, up to 8 decimal places are
        # allowed, precision which is unlikely to be exceeded by any standard
        # coordinate system. Round will return the appropriate value under 9
        # dps.
        coords = [round(coord, 8) for coord in coords]        

    # Unpack new coord values.
    min_x, min_y, max_x, max_y = coords
    
    # If aligning, first calculate the difference of the shortest length.
    if align:
        length = max_x - min_x
        height = max_y - min_y
        difference = length if length < height else height
        
        # Calculate rounding value, where floor(log10(difference)) gives the 
        # position of values. Subtracting this from the desired sig figs,
        # and an additional -1 gives the position of significant figures e.g. 
        # with a difference of 100 and sig_figs of 2, the output here is -1 dp, 
        # which round coords such as 12345 to 12340 or 12350.
        rounding_value = int(sig_figs-math.floor(math.log10(difference))-1)

        # If decimal places are to be kept (rounding_value > 0), set lambda
        # functions to round up max coords with ceil and down min coords with
        # floor.
        if rounding_value > 0:
            
            # The multiplier is used to round up or down when needed.
            multiplier = float('1' + '0' * rounding_value)
            
            # Round coord up with math.ceil, using multiplier to aquire the
            # required significant figures.
            ceil = lambda x: (int(math.ceil(x * multiplier)))/multiplier
            
            # Round coord up with math.floor, using multiplier to aquire the
            # required significant figures.
            floor = lambda x: (int(math.floor(x * multiplier)))/multiplier  

            # If applying a buffer, also round this value to match.
            if buffer_length:
                buffer_length = round(buffer_length, rounding_value)

        # If no decimal places will be used, set lambda functions to round 
        # coords to the required significant figures, and integer-ise the
        # outputs.
        else:
            
            # The multiplier will adjust coords where rounding would otherwise 
            # reduce the extent. e.g if rounding = -1, abs converts to 1, and
            # the output is 10, which will round coords +- 10 when needed.
            multiplier = int('1' + '0' * abs(rounding_value))
            
            # This rounds the coordinate to the required figures.
            rounded = lambda x: int(round(x, rounding_value))
            
            # Round coord, using multiplier to increase the coord value where
            # needed for max x,y coords.
            ceil = (lambda x: rounded(x) + multiplier if
                        rounded(x) < x else rounded(x))
                        
            # Round coord, using multiplier to decrease the coord value where
            # needed for min x,y values.
            floor = (lambda x: rounded(x) - multiplier if
                        rounded(x) > x else rounded(x))
                        
            # If applying a buffer, also round this value to match.
            if buffer_length:
                buffer_length = rounded(buffer_length)

        # Apply the selected lambda functions to the coordinates.
        max_x = ceil(max_x)
        max_y = ceil(max_y)
        min_x = floor(min_x)
        min_y = floor(min_y)
    
    # Adjust extents with buffer.
    if buffer_length:
        min_x -= buffer_length
        min_y -= buffer_length
        max_x += buffer_length
        max_y += buffer_length
    
    # Create extent array & return.
    min_xy = (min_x, min_y)
    max_xy = (max_x, max_y)
    extent = (min_xy, max_xy)
    return extent
    
    
#------------------------------------------------------------------------------
#  2. create_grid (function): Constructs a grid with square-shaped cells of
#     equal size, which overlaps the extent of the input extent object.
#------------------------------------------------------------------------------

def create_grid(extent, out_file, cell_size=0.0, proportion=0.05,
                spatial_ref=None):

    """
    Creates a polygon grid covering the entire extent of the input extent
    object. Each polygon in the grid has sides of equal length. The output grid
    will never be less than the input extent, so if the required cell size
    would produce a grid less than the input extent, the grid extent will be
    increased by an extra cell length.
    
    Arguments:

        extent (sequence):
            An array that must be formatted with two sub-sequences, the first
            containing the min x and min y coordinates of the extent, and the
            second the max equivalents. For example:
            extent = ((min_x, min_y)), ((max_x, max_y))
            
        out_file (str):
            Path for the output grid to be created.
        
        cell_size (float|int|long): 
            The size of cell lengths to build the grid from, in the units of
            the current workspace (optional).
        
        proportion (float):
            If cell size == 0, the proportion value will be used to generate
            a cell size. The proportion is the area of each cell as a
            proportion of the total extent, with the cell lengths rounded to
            the nearest whole number e.g. a value of 0.05 and an extent of 600
            m2 will produce a grid of cells sized 5 by 5 m (after rounding down
            from sqrt(600 * 0.05) (optional|default = 0.05).
        
        spatial_ref (object):
            arcpy.SpatialReference object, with the coordinate system and units
            of the output grid (optional).

    """
    
    # Delete any existing copy of the output file. 
    if arcpy.Exists(out_file):
        arcpy.Delete_management(out_file)
    
    # Set extent values.    
    min_x = extent[0][0]
    min_y = extent[0][1]
    max_x = extent[1][0]
    max_y = extent[1][1]
    length = max_x - min_x
    height = max_y - min_y
    
    # Determine an appropriate cell size from the proportion value (rounded to
    # a whole number, based on length).
    if not cell_size:
        cell_area = (length * height) * proportion
        cell_size = math.sqrt(cell_area)
        
        # If cell size will be a 3+ digits integer, round to an appropriate
        # value e.g. 5 & 6 digits = 3 sig figs, 7 & 8 = 4 sig figs. 
        if cell_size >= 100:
            rounding = int(round(float(len(str(int(cell_size)))) / 2))
            cell_size = round(cell_size, -rounding)
        
        # If the cell size is to be less than 100 map units, but more than 1,
        # round to 3 significant figures.
        elif cell_size >= 1:
            rounding_value = int(3-math.floor(math.log10(cell_size))-1)
            cell_size = round(cell_size, rounding_value)
 
        # If dealing with a very small cell size, round the value to the
        # nearest "half" value e.g. 0.0002367 will be rounded to 0.0002, and
        # 0.0136 to 0.015.
        else:
            rounding_value = 0
            for index, value in enumerate(str(math.modf(cell_size)[0])[2:]):                
                if all([rounding_value == 0 and value != '0']):
                    rounding_value = index + 2
            cell_size = round((cell_size / 5), rounding_value) * 5
    
    # Integer-ise cell size, if required.
    cell_size = int(cell_size) if int(cell_size) == cell_size else cell_size 
    
    # Create grid cells coordinates generator.
    coords_list = ([[j, i], [j + cell_size, i], [j + cell_size, i + cell_size],
                    [j, i + cell_size]] for i in
                    np.arange(min_y, max_y, cell_size) for j in
                    np.arange(min_x, max_x, cell_size))  
    
    # Create list of arcpy Polygons, and export as a final output file (this is
    # an alternative method to using the the buggy fishnet function). The
    # break_value variable interrupts processing to try and prevent memory
    # problems from occurring when building large, high resolution grids.
    feature_list = []
    break_value = 200000
    for count, feature in enumerate(coords_list, 1):
        array = arcpy.Array()
        for coord_pair in feature:
            point = arcpy.Point(float(coord_pair[0]), float(coord_pair[1]))
            array.add(point)
        if spatial_ref:
            polygon = arcpy.Polygon(array, spatial_ref)
        else:
            polygon = arcpy.Polygon(array)
        feature_list.append(polygon)
        if count == 100000:
            arcpy.CopyFeatures_management(feature_list, out_file)
            feature_list = []           
        elif count == break_value:
            arcpy.CopyFeatures_management(feature_list, r'in_memory\temp_grid')
            arcpy.Append_management(r'in_memory\temp_grid', out_file, 'NO_TEST')
            arcpy.Delete_management(r'in_memory\temp_grid')
            break_value += 100000
            feature_list = []
    if count < 100000:
        arcpy.CopyFeatures_management(feature_list, out_file)
    else:
        arcpy.CopyFeatures_management(feature_list, r'in_memory\temp_grid')
        arcpy.Append_management(r'in_memory\temp_grid', out_file, 'NO_TEST')
        arcpy.Delete_management(r'in_memory\temp_grid')

    return cell_size