# $Id: assoc.py,v 1.11 2003/09/29 16:51:35 wrobell Exp $

import app
import btest

import bazaar.exc

class OneToOneAssociationTestCase(btest.DBBazaarTestCase):
    """
    Test one-to-one associations.
    """

    def testLoading(self):
        """Test one-to-one association loading"""

        self.bazaar.getObjects(app.OrderItem)
        dbc = self.bazaar.motor.db_conn.cursor()
        dbc.execute('select __key__, "order_fkey", pos, article_fkey from order_item')
        row = dbc.fetchone()
        while row:
            order_item = self.bazaar.brokers[app.OrderItem].cache[row[0]]

            # check the value of foreign key
            self.assertEqual(order_item.article_fkey, row[3], \
                'article foreign key mismatch "%s" != "%s"' % (order_item.article_fkey, row[3]))

            # check the value of associated object's primary key
            self.assertEqual(order_item.article.__key__, row[3], \
                'article primary key mismatch "%s" != "%s"' % (order_item.article.__key__, row[3]))

            row = dbc.fetchone()


    def testUpdating(self):
        """Test one-to-one association updating"""
        pass



class ManyToManyAssociationTestCase(btest.DBBazaarTestCase):
    """
    Test many-to-many associations.
    """
    def checkEmpAsc(self):
        self.checkListAsc(app.Employee, 'orders', \
            'select employee, "order" from employee_orders order by employee, "order"')


    def testLoading(self):
        """Test many-to-many association loading
        """
        self.checkEmpAsc()


    def testReloading(self):
        """Test many-to-many association loading
        """
        emp = self.bazaar.getObjects(app.Employee)[0]
        orders = emp.orders

        # remove some referenced objects
        assert len(orders) > 0
        for o in orders:
            del orders[o]
        assert len(orders) == 0

        # reload data and check if they are reloaded
        app.Employee.orders.reloadData()
        self.checkEmpAsc()


    def testAppending(self):
        """Test appending objects to many-to-many association
        """
        emp = self.bazaar.getObjects(app.Employee)[0]

        ord1 = app.Order()
        ord1.no = 1002
        ord1.finished = False

        ord2 = app.Order()
        ord2.no = 1003
        ord2.finished = False

        # append object with _defined_ primary key value
        self.bazaar.add(ord1)
        emp.orders.append(ord1)

        # append object with _undefined_ primary key value
        emp.orders.append(ord2)
        self.bazaar.add(ord2)
        self.assert_(ord1 in emp.orders, \
            'appended referenced object not found in association %s -> %s' % \
            (emp, ord1))
        self.assert_(ord2 in emp.orders, \
            'appended referenced object not found in association %s -> %s' % \
            (emp, ord2))
        emp.orders.update()
        self.checkEmpAsc()

        # append object with undefined primary key value
        ord1 = app.Order()
        ord1.no = 1002
        ord1.finished = False
        emp.orders.append(ord1)
        self.assertRaises(app.db_module.ProgrammingError, emp.orders.update)
        self.bazaar.rollback()

        self.assertRaises(bazaar.exc.AssociationError, emp.orders.append, None)
        self.assertRaises(bazaar.exc.AssociationError, emp.orders.append, object())
        self.assertRaises(bazaar.exc.AssociationError, emp.orders.append, ord1)


    def testRemoving(self):
        """Test removing objects from many-to-many association
        """
        emp = self.bazaar.getObjects(app.Employee)[0]
        assert len(emp.orders) > 0
        orders = list(emp.orders)
        ord = orders[0]
        del emp.orders[ord]
        self.assert_(ord not in emp.orders, \
            'removed referenced object found in association')
        emp.orders.update()
        self.checkEmpAsc()
        self.assertRaises(bazaar.exc.AssociationError, emp.orders.remove, None)
        self.assertRaises(bazaar.exc.AssociationError, emp.orders.remove, object())
        self.assertRaises(bazaar.exc.AssociationError, emp.orders.remove, ord)


    def testMixedUpdate(self):
        """Test appending and removing objects to/from many-to-many association
        """
        emp = self.bazaar.getObjects(app.Employee)[0]

        ord1 = app.Order()
        ord1.no = 1002
        ord1.finished = False

        ord2 = app.Order()
        ord2.no = 1003
        ord2.finished = False

        # append object with _defined_ primary key value
        self.bazaar.add(ord1)
        emp.orders.append(ord1)

        assert len(emp.orders) > 0
        orders = list(emp.orders)
        ord = orders[0]
        # fixme: improve test code, so assertion below is not required
        assert ord != ord2 != ord1
        del emp.orders[ord]

        # append object with _undefined_ primary key value
        emp.orders.append(ord2)
        self.bazaar.add(ord2)

        self.assert_(ord not in emp.orders, \
            'removed referenced object found in association')
        self.assert_(ord1 in emp.orders, \
            'appended referenced object not found in association')
        self.assert_(ord2 in emp.orders, \
            'appended referenced object not found in association')

        emp.orders.update()

        self.assert_(ord not in emp.orders, \
            'removed referenced object found in association')

        self.assert_(ord1 in emp.orders, \
            'appended referenced object not found in association')
        self.assert_(ord2 in emp.orders, \
            'appended referenced object not found in association')

        self.checkEmpAsc()

        emp.orders.append(ord)
        emp.orders.remove(ord1)
        emp.orders.remove(ord2)

        self.assert_(ord in emp.orders, \
            'appended referenced object not found in association')
        self.assert_(ord1 not in emp.orders, \
            'removed referenced object found in association')
        self.assert_(ord2 not  in emp.orders, \
            'removed referenced object found in association')

        emp.orders.update()

        self.assert_(ord in emp.orders, \
            'appended referenced object not found in association')
        self.assert_(ord1 not in emp.orders, \
            'removed referenced object found in association')
        self.assert_(ord2 not  in emp.orders, \
            'removed referenced object found in association')

        self.checkEmpAsc()



class OneToManyAssociationTestCase(btest.DBBazaarTestCase):
    """
    Test one-to-many associations.
    """
    def checkOrdAsc(self):
        self.checkListAsc(app.Order, 'items', \
            'select order_fkey, __key__  from order_item where order_fkey is not null order by order_fkey, __key__')


    def testLoading(self):
        """Test one-to-many association loading
        """
        self.checkOrdAsc()


    def testReloading(self):
        """Test one-to-many association loading
        """
        ord = self.bazaar.getObjects(app.Order)[0]
        # remove all of referenced objects
        assert len(ord.items) > 0
        for oi in ord.items:
            del ord.items[oi]
        assert len(ord.items) == 0

        # reload data and check if they are reloaded
        app.Order.items.reloadData()
        self.checkOrdAsc()


    def testAppending(self):
        """Test appending objects to one-to-many association
        """
        ord = self.bazaar.getObjects(app.Order)[0]
        art = self.bazaar.getObjects(app.Article)[0]

        oi1 = app.OrderItem()
        oi1.pos = 1000
        oi1.quantity = 10.3
        oi1.article = art

        oi2 = app.OrderItem()
        oi2.pos = 1001
        oi2.quantity = 10.4
        oi2.article = art

        # append object with _defined_ primary key value
        self.bazaar.add(oi1)
        ord.items.append(oi1)

        # append object with _undefined_ primary key value
        ord.items.append(oi2)
        self.bazaar.add(oi2)
        self.assert_(oi1 in ord.items, \
            'appended referenced object not found in association %s -> %s' % \
            (ord, oi1))
        self.assert_(oi2 in ord.items, \
            'appended referenced object not found in association %s -> %s' % \
            (ord, oi2))
        ord.items.update()
        self.checkOrdAsc()

        self.assertRaises(bazaar.exc.AssociationError, ord.items.append, None)
        self.assertRaises(bazaar.exc.AssociationError, ord.items.append, object())
        self.assertRaises(bazaar.exc.AssociationError, ord.items.append, oi1)


    def testRemoving(self):
        """Test removing objects from one-to-many association
        """
        ord = self.bazaar.getObjects(app.Order)[0]
        assert len(ord.items) > 0
        items = list(ord.items)
        oi = items[0]
        del ord.items[oi]
        self.assert_(oi not in ord.items, \
            'removed referenced object found in association')
        ord.items.update()
        self.checkOrdAsc()
        self.assertRaises(bazaar.exc.AssociationError, ord.items.remove, None)
        self.assertRaises(bazaar.exc.AssociationError, ord.items.remove, object())
        self.assertRaises(bazaar.exc.AssociationError, ord.items.remove, oi)


    def testMixedUpdate(self):
        """Test appending and removing objects to/from one-to-many association
        """
        ord = self.bazaar.getObjects(app.Order)[0]
        art = self.bazaar.getObjects(app.Article)[0]

        oi1 = app.OrderItem()
        oi1.pos = 1000
        oi1.quantity = 10.3
        oi1.article = art

        oi2 = app.OrderItem()
        oi2.pos = 1001
        oi2.quantity = 10.4
        oi2.article = art

        # append object with _defined_ primary key value
        self.bazaar.add(oi1)
        ord.items.append(oi1)

        assert len(ord.items) > 0
        items = list(ord.items)
        oi = items[0]
        # fixme: improve test code, so assertion below is not required
        assert oi != oi2 != oi1
        del ord.items[oi]

        # append object with _undefined_ primary key value
        ord.items.append(oi2)
        self.bazaar.add(oi2)

        self.assert_(oi not in ord.items, \
            'removed referenced object found in association')
        self.assert_(oi1 in ord.items, \
            'appended referenced object not found in association')
        self.assert_(oi2 in ord.items, \
            'appended referenced object not found in association')

        ord.items.update()

        self.assert_(oi not in ord.items, \
            'removed referenced object found in association')

        self.assert_(oi1 in ord.items, \
            'appended referenced object not found in association')
        self.assert_(oi2 in ord.items, \
            'appended referenced object not found in association')

        self.checkOrdAsc()

        ord.items.append(oi)
        ord.items.remove(oi1)
        ord.items.remove(oi2)

        self.assert_(oi in ord.items, \
            'appended referenced object not found in association')
        self.assert_(oi1 not in ord.items, \
            'removed referenced object found in association')
        self.assert_(oi2 not  in ord.items, \
            'removed referenced object found in association')

        ord.items.update()

        self.assert_(oi in ord.items, \
            'appended referenced object not found in association')
        self.assert_(oi1 not in ord.items, \
            'removed referenced object found in association')
        self.assert_(oi2 not  in ord.items, \
            'removed referenced object found in association')

        self.checkOrdAsc()
