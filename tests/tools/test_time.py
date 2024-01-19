import unittest
from decimal import Decimal

from mnms.time import Time, Dt


class TestTime(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_time(self):
        t = Time("07:34:23.67")
        self.assertEqual(7, t._hours)
        self.assertEqual(34, t._minutes)
        self.assertAlmostEqual(23.67, t.seconds)

    def test_time_from_seconds(self):
        t = Time.from_seconds(12345)
        self.assertEqual(3, t.hours)
        self.assertEqual(25, t.minutes)
        self.assertAlmostEqual(45, t.seconds)

    def test_time_from_dt(self):
        t = Time.from_dt(Dt(7, 34, 23.67))
        self.assertEqual(7, t._hours)
        self.assertEqual(34, t._minutes)
        self.assertAlmostEqual(23.67, t.seconds)

    def test_time_operator(self):
        t1 = Time("07:34:23.67")
        t2 = Time("07:34:23.69")

        self.assertTrue(t1 < t2)
        self.assertTrue(t1 <= t2)
        self.assertTrue(t2 > t1)
        self.assertTrue(t2 >= t1)

        self.assertTrue(t1 < t2)
        self.assertTrue(t2 > t1)

        t2 = Time("07:34:23.67")
        self.assertTrue(t1 == t2)
        self.assertTrue(t1 >= t2)
        self.assertTrue(t1 <= t2)

        repr(t1)


class TestDt(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_dt(self):
        dt = Dt(12, 35, 13.45)

        self.assertEqual(12, dt._hours)
        self.assertEqual(35, dt._minutes)
        self.assertAlmostEqual(Decimal(13.45), dt._seconds)

        dt = Dt(12, 135, 73.45)

        self.assertEqual(14, dt._hours)
        self.assertEqual(16, dt._minutes)
        self.assertAlmostEqual(Decimal(13.45), dt._seconds)

    def test_to_sec(self):
        dt = Dt(12, 35, 13.45)
        self.assertAlmostEqual(12*3600+35*60+13.45, dt.to_seconds())

    def test_mul_dt(self):
        dt = Dt(12, 35, 13.45)*2
        self.assertEqual(25, dt._hours)
        self.assertEqual(10, dt._minutes)
        self.assertAlmostEqual(Decimal(13.45*2), dt._seconds)

    def test_add_dt(self):
        dt = Dt(12, 35, 13.45) + Dt(1, 30, 10)
        self.assertEqual(14, dt._hours)
        self.assertEqual(5, dt._minutes)
        self.assertAlmostEqual(Decimal(23.45), dt._seconds)

    def test_sub_dt(self):
        dt = Dt(12, 35, 13.45) - Dt(13, 40, 20)
        self.assertEqual(22, dt._hours)
        self.assertEqual(54, dt._minutes)
        self.assertAlmostEqual(Decimal(53.45), dt._seconds)

    def test_dt_operator(self):
        dt1 = Dt(7, 34, 23.67)
        dt2 = Dt(7, 34, 23.69)

        self.assertTrue(dt1 < dt2)
        self.assertTrue(dt1 <= dt2)
        self.assertTrue(dt2 > dt1)
        self.assertTrue(dt2 >= dt1)

        self.assertTrue(dt1 < dt2)
        self.assertTrue(dt2 > dt1)

        dt2 = Dt(7, 34, 23.67)
        self.assertTrue(dt1 == dt2)
        self.assertTrue(dt1 >= dt2)
        self.assertTrue(dt1 <= dt2)

        repr(dt1)