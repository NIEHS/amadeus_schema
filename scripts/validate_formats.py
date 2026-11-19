"""Semantic format checks supplementing LinkML structural validation.

Suffixes are discovery hints. This checker never claims to inspect remote bytes.
"""
from pathlib import PurePosixPath


def check_format_details(details):
    def require(test, message):
        if not test:
            raise ValueError('format_details: ' + message)
    family = details.get('format_family')
    variant = details.get('format_variant')
    model = details.get('data_model')
    container = details.get('physical_container')
    require(model is None or family == 'netcdf', 'data_model applies only to NetCDF')
    if variant in ('netcdf3_classic', 'netcdf3_64bit_offset', 'netcdf3_64bit_data'):
        require(family == 'netcdf' and model in (None, 'classic') and container in (None, 'cdf'),
                'NetCDF-3 requires classic model and CDF container')
    if variant == 'netcdf4':
        require(family == 'netcdf' and container in (None, 'hdf5'), 'NetCDF-4 uses HDF5')
    if details.get('expected_filename_extensions_scope') == 'catalog_family':
        require(bool(details.get('catalog_family')), 'family scope requires catalog_family')
    for field in ('expected_filename_extensions', 'package_filename_extensions', 'companion_filename_extensions'):
        values = details.get(field) or []
        require(len(values) == len(set(values)), f'duplicate {field}')
    for status in ('cf_conformance_status', 'profile_conformance_status'):
        if details.get(status) in ('conformant', 'nonconformant'):
            require(details['identification']['basis'] == 'validator_report',
                    'conformance findings require a validator report')
    if details.get('format_profile') == 'cloud_optimized_geotiff':
        require(family == 'tiff', 'COG profile requires TIFF')


def check_catalog_formats(document):
    for collection in ('products', 'assets'):
        for record in document.get(collection) or []:
            if record.get('format_details') is not None:
                check_format_details(record['format_details'])
            if collection == 'assets':
                filename, extension = record.get('filename'), record.get('filename_extension')
                if filename and (PurePosixPath(filename).name != filename or '\\' in filename):
                    raise ValueError('Asset filename must be a basename')
                if extension and (not filename or not filename.lower().endswith(extension)):
                    raise ValueError('Asset filename_extension disagrees with filename')
