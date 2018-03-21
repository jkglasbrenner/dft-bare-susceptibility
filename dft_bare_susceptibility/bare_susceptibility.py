# -*- coding: utf-8; -*-

# Modules
from bare_susceptibility import dx_file_reader
import numpy as np


# Classes
class Bandstructure(object):
    """
    The Bandstructure class reads, stores, and transforms the eigenvalues in
    reciprocal space that are calculated using a density functional theory
    calculation.
    """

    def __init__(self):
        """
        Instantiates the Bandstructure class
        """
        self.eigenvalues = None
        self.reciprocal_vectors = None
        self.origin = None

    def read_file(self, file_path):
        (self.reciprocal_vectors,
         self.origin,
         self.eigenvalues) = dx_file_reader.extract_from_dx_file(file_path)

    def get_reciprocal_vectors(self):
        return self.reciprocal_vectors

    def get_eigenvalues(self):
        return self.eigenvalues

    def get_origin(self):
        return self.origin


# Functions
def chi_calculation(eigenvalues, gamma, temperature):
    nbands = eigenvalues.shape[0]
    nqpts = eigenvalues.shape[1:]
    chi = np.zeros(nqpts, dtype=np.complex)
    it = np.nditer(chi, flags=['multi_index'], op_flags=['readwrite'])
    fermi_function_eigenvalues = fermi_function(
        eigenvalues / temperature
    )
    e_alpha = np.repeat(eigenvalues,
                        nbands,
                        axis=0)
    fermi_function_e_alpha = np.repeat(fermi_function_eigenvalues,
                                       nbands,
                                       axis=0)
    for chi_at_q in it:
        indx_qx, indx_qy, indx_qz = it.multi_index
        eigenvalues_q_shift = shift_eigenvalues_by_q(
            eigenvalues, indx_qx, indx_qy, indx_qz)
        fermi_function_eigenvalues_q_shift = shift_eigenvalues_by_q(
            fermi_function_eigenvalues, indx_qx, indx_qy, indx_qz)
        e_beta = np.tile(
            eigenvalues_q_shift,
            (nbands, 1, 1, 1)
        )
        fermi_function_e_beta = np.tile(
            fermi_function_eigenvalues_q_shift,
            (nbands, 1, 1, 1)
        )
        chi_at_q += chi_at_q_band_summation(
            e_alpha, fermi_function_e_alpha,
            e_beta, fermi_function_e_beta,
            gamma, temperature
        )
    return chi / nqpts[0] / nqpts[1] / nqpts[2] / 2


def chi_at_q_band_summation(e_alpha, fermi_function_e_alpha,
                            e_beta, fermi_function_e_beta,
                            gamma, temperature):
    return np.sum(
        (
            fermi_function_e_alpha - fermi_function_e_beta
        ) / (
            e_beta - e_alpha + gamma * 1.0j
        )
    )


def shift_eigenvalues_by_q(eigenvalues, indx_qx, indx_qy, indx_qz):
    return np.roll(
        a=eigenvalues,
        shift=(indx_qx, indx_qy, indx_qz),
        axis=(1, 2, 3))


def fermi_function(x):
    return (1.0 + 0.0j) / (np.exp(x) + (1.0 + 0.0j))


def main(in_file_path, out_file_path, gamma, temperature):
    bandstructure = Bandstructure()
    bandstructure.read_file(in_file_path)
    reciprocal_vectors = bandstructure.get_reciprocal_vectors()
    eigenvalues = bandstructure.get_eigenvalues()
    origin = bandstructure.get_origin()
    chi = chi_calculation(eigenvalues[:, :-1, :-1, :-1].astype(np.complex),
                          gamma, temperature)
    chi = dx_file_reader.expand_data_range(chi)
    dx_file_reader.write_file(
        chi,
        reciprocal_vectors[0],
        reciprocal_vectors[1],
        reciprocal_vectors[2],
        origin,
        out_file_path)
