import os
import shutil
import tempfile
from urllib.request import urlopen
import zipfile

from django.contrib.gis.gdal import DataSource
from django.contrib.gis.utils import LayerMapping
from django.core.management.base import CommandError
from django.core.management.base import BaseCommand


from localflavor.us.us_states import US_STATES

from ...models import Neighborhood, neighborhood_mapping


class Command(BaseCommand):
    help = "Import Zillow neighborhood boundaries"
    output_transaction = True
    requires_model_validation = False
    
    def handle(self, **options):
        ZILLOW_SHAPEFILE_URL = 'https://www.zillowstatic.com/static-neighborhood-boundaries/LATEST/static-neighborhood-boundaries/shp/ZillowNeighborhoods-%s.zip'
        ZILLOW_SHAPEFILE_DIR = tempfile.mkdtemp()

        try:
            # Clear neighborhood table
            Neighborhood.objects.all().delete()

            for abbrev, name in US_STATES:
                self.stdout.write('Importing %s neighborhoods\n' % abbrev)

                # Fetch the zipped shapefile from Zillow
                url = ZILLOW_SHAPEFILE_URL % abbrev
                try:
                    zip_file = download(url)
                except Exception as exc:
                    print('Could not download', abbrev, exc)
                    return

                # Extract and import the shapefile
                try:
                    zipfile.ZipFile(zip_file).extractall(ZILLOW_SHAPEFILE_DIR)
                    shapefile = os.path.join(ZILLOW_SHAPEFILE_DIR, 'ZillowNeighborhoods-%s.shp' % abbrev)
                    import_neighborhoods_shapefile(shapefile)
                finally:
                    zip_file.close()
        finally:
            shutil.rmtree(ZILLOW_SHAPEFILE_DIR)

def import_neighborhoods_shapefile(shapefile):
    """Import Zillow neighborhood boundaries from a shapefile"""

    # Load the shapefile
    ds = DataSource(shapefile)

    # Import the neighborhoods
    lm = LayerMapping(Neighborhood, ds, neighborhood_mapping,
                      transform=False, encoding='iso-8859-1')
    lm.save(strict=True, verbose=False)

def download(url):
    """Helper function to download a file to a temporary location."""
    remote = urlopen(url)
    local = tempfile.TemporaryFile()
    try:
        shutil.copyfileobj(remote, local)
    except:
        local.close()
        raise
    finally:
        remote.close()
    return local
