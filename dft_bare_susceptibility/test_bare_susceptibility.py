# -*- coding: utf-8; -*-

# Modules
from bare_susceptibility import bare_susceptibility
import numpy as np
import pytest
import os


@pytest.fixture(scope="module")
def bandstructure_from_dx_test_file():
    test_file_path = "./bare_susceptibility/tests/cfa122_eigenvalues.dx.gz"
    Bandstructure = bare_susceptibility.Bandstructure()
    Bandstructure.read_file(test_file_path)
    return Bandstructure


class TestBandstructureDxFile(object):
    def test_Bandstructure_eigenvalues(
            self, bandstructure_from_dx_test_file):
        Bandstructure = bandstructure_from_dx_test_file
        assert hasattr(Bandstructure, 'eigenvalues')
        eigenvalues = Bandstructure.get_eigenvalues()
        assert isinstance(eigenvalues, np.ndarray)
        for dimensions in eigenvalues.shape:
            assert dimensions > 0

    def test_Bandstructure_reciprocal_vectors(
            self, bandstructure_from_dx_test_file):
        Bandstructure = bandstructure_from_dx_test_file
        assert hasattr(Bandstructure, 'reciprocal_vectors')
        reciprocal_vectors = Bandstructure.get_reciprocal_vectors()
        assert isinstance(reciprocal_vectors, np.ndarray)
        for dimensions in reciprocal_vectors.shape:
            assert dimensions > 0
