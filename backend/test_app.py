import unittest
from app import app, explain, components, devices

class PartweaveRulesTest(unittest.TestCase):
    def test_known_ram_is_compatible(self):
        result = explain(components[0], devices[0])
        self.assertEqual(result['status'], 'compatible')
        self.assertTrue(result['reasons'])

    def test_wrong_ram_type_is_incompatible(self):
        part = dict(components[0], specs=dict(components[0]['specs'], ram_type='DDR3 SO-DIMM'))
        result = explain(part, devices[0])
        self.assertEqual(result['status'], 'incompatible')

    def test_missing_spec_is_potential(self):
        part = dict(components[0], specs={'ram_type': 'DDR4 SO-DIMM'})
        result = explain(part, devices[0])
        self.assertEqual(result['status'], 'potential')
        self.assertIn('capacity', result['unknown'])

    def test_health_route(self):
        response = app.test_client().get('/api/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'ok')

if __name__ == '__main__':
    unittest.main()
