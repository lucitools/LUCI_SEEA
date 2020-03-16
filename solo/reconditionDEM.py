import arcpy
from arcpy.sa import EucDistance, Con, IsNull, Raster

import LUCI_SEEA.lib.log as log
from LUCI_SEEA.lib.refresh_modules import refresh_modules
refresh_modules([log])

def function(DEM, streamNetwork, smoothDropBuffer, smoothDrop, streamDrop, outputReconDEM):

    try:
        # Set environment variables
        arcpy.env.extent = DEM
        arcpy.env.mask = DEM
        arcpy.env.cellSize = DEM

        # Set temporary variables
        prefix = "recon_"
        streamRaster = prefix + "streamRaster"

        # Determine DEM cell size and OID column name
        size = arcpy.GetRasterProperties_management(DEM, "CELLSIZEX")
        OIDField = arcpy.Describe(streamNetwork).OIDFieldName

        # Convert stream network to raster
        arcpy.PolylineToRaster_conversion(streamNetwork, OIDField, streamRaster, "", "", size)

        # Work out distance of cells from stream
        distanceFromStream = EucDistance(streamRaster, "", size)

        # Elements within a buffer distance of the stream are smoothly dropped
        intSmoothDrop = Con(distanceFromStream > float(smoothDropBuffer), 0,
                            (float(smoothDrop) / float(smoothDropBuffer)) * (float(smoothDropBuffer) - distanceFromStream))
        del distanceFromStream

        # Burn this smooth drop into DEM. Cells in stream are sharply dropped by the value of "streamDrop"
        binaryStream = Con(IsNull(Raster(streamRaster)), 0, 1)
        reconDEMTemp = Raster(DEM) - intSmoothDrop - (float(streamDrop) * binaryStream)
        del intSmoothDrop
        del binaryStream
        
        reconDEMTemp.save(outputReconDEM)
        del reconDEMTemp

        log.info("Reconditioned DEM generated")

    except Exception:
        log.error("DEM reconditioning function failed")
        raise
