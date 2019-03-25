# Copyright (c) 2017-2019 Keiron O'Shea
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA 02110-1301 USA


from .utils import terms
import numpy as np
from scipy.stats import binned_statistic
import math


class Scan:
    def __init__(self,
                 pymzml_spectrum,
                 snr_estimator: str = False,
                 peak_type: str = "raw"):
        """
            Initalise a Scan object for a given pymzML Spectrum.

            Args:
                pymzml_spectrum (pymzml.Spectrum): Spectrum object

        """
        self.pymzml_spectrum = pymzml_spectrum
        self.polarity = self._get_polarity()

        self.peak_type = peak_type

        if snr_estimator:
            self.snr = self._estimate_snr(snr_estimator)
        else:
            self.snr = False

        self.masses, self.intensities = self._get_spectrum()

        self.total_ion_count = self._calculate_total_ion_count()

        self.mass_range = self._calculate_mass_range()

    def _estimate_snr(self, snr_estimator):
        return self.pymzml_spectrum.estimated_noise_level(mode=snr_estimator)

    def _calculate_total_ion_count(self):
        return np.sum(self.intensities)

    def _calculate_mass_range(self):
        return [np.min(self.masses), np.max(self.masses)]

    def _get_spectrum(self):
        try:
            peaks = getattr(self.pymzml_spectrum, "peaks")(self.peak_type)

            masses, intensities = [np.array(x) for x in zip(*peaks)]

            if self.snr:
                not_noise = intensities >= self.snr
                masses = masses[not_noise]
                intensities = intensities[not_noise]

            return np.array(masses), np.array(intensities)

        except ValueError:
            raise ValueError("%s is not a supported peak type." % (self.peak_type))

    def bin(self, bin_width: float = 0.01, statistic: str = "mean"):
        min_mass, max_mass = self.mass_range

        min_mass = math.floor(min_mass)
        max_mass = math.ceil(max_mass)+bin_width

        bins = np.arange(min_mass, max_mass, bin_width)

        binned_intensities, _, _ = binned_statistic(
            self.masses,
            self.intensities,
            statistic = statistic,
            bins = bins
        )

        binned_masses, _, _= binned_statistic(
            self.masses,
            self.masses,
            statistic = statistic,
            bins = bins
        )

        index = ~np.isnan(binned_intensities)

        self.masses = binned_masses[index]
        self.intensities = binned_intensities[index]
    
    def _get_polarity(self):
        polarity = None
        for polarity_accession in terms["polarity"].keys():
            if self.pymzml_spectrum.get(polarity_accession) != None:
                polarity = terms["polarity"][polarity_accession]
        return polarity
