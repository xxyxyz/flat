import unittest

class TestColors(unittest.TestCase):
    def test_svg_rgba(self):
        from flat import color
        c = color.rgba(1, 2, 3, 4)
        self.assertEqual(b'rgba(1,2,3,0.0157)', c.svg())

if __name__ == '__main__':
    unittest.main()
