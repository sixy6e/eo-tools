#!/usr/bin/env python

from __future__ import absolute_import
import numpy
import ogr
import pandas

from image_processing.segmentation.rasterise import project_vector


def spatial_intersection(base_vector_fname, input_vector_fname, envelope=True):
    """
    Performs a spatial intersection of feature geometry to and
    returns a list of FID's from the base vector file.

    :param base_vector_fname:
        A string containing the full file path name to an
        OGR compliant vector file. This file will be used to select
        features from.

    :param input_vector_fname:
        A string containing the full file path name to an
        OGR compliant vector file.

    :param envelope:
        If set to True (Default), then the envelope of each feature
        will be used rather than the geometry of the feature to perform
        intersection.

    :return:
        A `list` containing the FID's of the base vector.
    """
    vec_ds1 = ogr.Open(input_vector_fname)
    vec_ds2 = ogr.Open(base_vector_fname)
    lyr1 = vec_ds1.GetLayer()
    lyr2 = vec_ds2.GetLayer()

    prj1 = lyr1.GetSpatialRef()
    prj2 = lyr2.GetSpatialRef()

    # Transfrom the geometry as needed
    if not prj1.IsSame(prj2):
        project_vector(lyr1, prj1, prj2)

    fids = []

    if envelope:
        for feat2 in lyr2:
            geom = feat2.GetGeometryRef()
            xmin, xmax, ymin, ymax = geom.GetEnvelope()
            lyr1.SetSpatialFilterRect(xmin, ymin, xmax, ymax)
            for feat1 in lyr1:
                fids.append(feat1.GetFID())
            lyr1.SetSpatialFilter(None)
    else:
        for feat2 in lyr2:
            ref = feat2.GetGeometryRef()
            lyr1.SetSpatialFilter(ref)
            for feat1 in lyr1:
                fids.append(feat1.GetFID())
            lyr1.SetSpatialFilter(None)

    fids = numpy.unique(numpy.array(fids)).tolist()

    return fids


def retrieve_attribute_table(layer):
    """
    Retrieves the attribute table for the input vector layer.

    :param layer:
        An ogr `Layer` object.

    :return:
        A `pandas.DataFrame` containing the attribute table.
    """
    defn = layer.GetLayerDefn()
    cols = []
    cols.append('FID')

    for i in range(defn.GetFieldCount()):
        name = defn.GetFieldDefn(i).GetName()
        cols.append(name)

    df = pandas.DataFrame(columns=cols)
    table = {}

    for feat in layer:
        table['FID'] = feat.GetFID()
        for key in feat.keys():
            table[key] = feat.GetField(key)
        df = df.append(table, ignore_index=True)

    return df