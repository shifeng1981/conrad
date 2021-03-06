"""
Unit tests for :mod:`conrad.medicine.anatomy`.
"""
"""
Copyright 2016 Baris Ungun, Anqi Fu

This file is part of CONRAD.

CONRAD is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

CONRAD is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with CONRAD.  If not, see <http://www.gnu.org/licenses/>.
"""
from conrad.compat import *

import numpy as np

from conrad.medicine.structure import Structure
from conrad.medicine.anatomy import *
from conrad.tests.base import *

class AnatomyTestCase(ConradTestCase):
	@classmethod
	def setUpClass(self):
		self.A0 = A0 = np.random.rand(500, 50)
		self.A1 = A1 = np.random.rand(200, 50)
		self.structures = [
				Structure(0, 'oar', False, A=A0),
				Structure(1, 'ptv', True, A=A1)
		]

	def setUp(self):
		self.x_random = np.random.rand(50)

	def test_anatomy_init(self):
		a = Anatomy()
		self.assertIsInstance( a.structures, dict )
		self.assertEqual( len(a.structures), 0 )
		self.assertTrue( a.is_empty )
		self.assertEqual( a.n_structures, 0 )
		self.assertEqual( a.size, 0 )
		self.assertFalse( a.plannable )

	def test_structure_add_remove(self):
		a = Anatomy()

		# add OAR
		a += Structure('label1', 'oar', False)
		self.assertFalse( a.is_empty )
		self.assertEqual( a.n_structures, 1 )
		self.assertFalse( a.plannable )

		self.assert_nan( a.size )
		a['label1'].A_full = np.random.rand(500, 100)
		self.assertEqual( a.size, 500 )
		self.assertFalse( a.plannable )

		a += Structure('label2', 'ptv', True)
		self.assertFalse( a.plannable )
		a['label2'].A_full = np.random.rand(500, 100)
		self.assertEqual( a.n_structures, 2 )
		self.assertEqual( a.size, 1000 )
		self.assertTrue( a.plannable )

		self.assertIn( 'label1', a.labels )
		self.assertIn( 'label2', a.labels )

		a -= 'label1'
		self.assertEqual( a.n_structures, 1 )
		self.assertEqual( a.size, 500 )
		self.assertNotIn( 'label1', a.labels )
		self.assertTrue( a.plannable )

		a -= 'ptv'
		self.assertTrue( a.is_empty )
		self.assertEqual( a.n_structures, 0 )
		self.assertEqual( a.size, 0 )
		self.assertNotIn( 'label2', a.labels )
		self.assertFalse( a.plannable )

		structure_list = [
				Structure(0, 'oar', False),
				Structure(1, 'ptv', True)
		]

		a.structures = self.structures
		self.assertEqual( a.n_structures, 2 )
		self.assertIn( 0, a.labels )
		self.assertIn( 1, a.labels )

		a2 = Anatomy(self.structures)
		self.assertEqual( a2.n_structures, 2 )
		self.assertIn( 0, a2.labels )
		self.assertIn( 1, a2.labels )

		a3 = Anatomy(a)
		self.assertEqual( a3.n_structures, 2 )
		self.assertIn( 0, a3.labels )
		self.assertIn( 1, a3.labels )

	def test_dose_calc_and_summary(self):
		a = Anatomy(self.structures)
		y0 = self.A0.dot(self.x_random)
		y1 = self.A1.dot(self.x_random)

		a.calculate_doses(self.x_random)
		self.assert_vector_equal( y0, a[0].y )
		self.assert_vector_equal( y1, a[1].y )

		# test satisfaction of some patently true constraints
		constraints = {
			'oar': ['D100 < 1000 Gy', 'D0 < 1000 Gy'],
			'ptv': ['D100 < 1000 Gy', 'D0 < 1000 Gy'],
		}
		self.assertTrue( a.satisfies_prescription(constraints) )

		ds = a.dose_summary_data()
		for s in self.structures:
			self.assertIn( s.label, ds )
			self.assertIn( 'min', ds[s.label] )
			self.assertIn( 'mean', ds[s.label] )
			self.assertIn( 'max', ds[s.label] )
			self.assertIn( 'D2', ds[s.label] )
			self.assertIn( 'D98', ds[s.label] )

		ds = a.dose_summary_data(percentiles=[1])
		for s in self.structures:
			self.assertIn( s.label, ds )
			self.assertIn( 'min', ds[s.label] )
			self.assertIn( 'mean', ds[s.label] )
			self.assertIn( 'max', ds[s.label] )
			self.assertIn( 'D1', ds[s.label] )
			self.assertNotIn( 'D2', ds[s.label] )
			self.assertNotIn( 'D98', ds[s.label] )

		ds = a.dose_summary_data(percentiles=[10, 22, 83])
		for s in self.structures:
			self.assertIn( s.label, ds )
			self.assertIn( 'D10', ds[s.label] )
			self.assertIn( 'D22', ds[s.label] )
			self.assertIn( 'D83', ds[s.label] )

		ds = a.dose_summary_data(percentiles=xrange(10, 100, 10))
		for s in self.structures:
			self.assertIn( s.label, ds )
			for p in xrange(10, 100, 10):
				self.assertIn( 'D{}'.format(p), ds[s.label] )

		ds = a.dose_summary_string
		for s in self.structures:
			self.assertIn( s.summary_string, ds )