import ee
import json

ee.Initialize(project='ee-geomaticape-1') # Replace with a valid project if needed, or use without project if local auth is sufficient

# Try to get an image and test the mask logic
def test_mask():
    aoi = ee.Geometry.Point([-76.0, -10.0])
    col = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(aoi).filterDate('2023-01-01', '2023-12-31')
    img = ee.Image(col.first())
    
    qa = img.select('QA_PIXEL')
    
    mask = qa.bitwiseAnd(8).eq(0)
    
    # Check if the mask actually masks anything
    dict_res = mask.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=aoi,
        scale=30
    ).getInfo()
    
    print("Mean of mask (should be < 1 if there are clouds, or 1 if clear):", dict_res)

test_mask()
