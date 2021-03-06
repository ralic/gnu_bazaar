# $Id: __init__.py,v 1.21 2005/05/13 17:15:58 wrobell Exp $
#
# Bazaar ORM - an easy to use and powerful abstraction layer between relational
# database and object oriented application.
#
# Copyright (C) 2000-2005 by Artur Wroblewski <wrobell@pld-linux.org>
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
Bazaar ORM is an easy to use and powerful abstraction layer between
relational database and object oriented application.

Features:
    - easy to use - define classes and programmer is ready to get and modify
      application data in object-oriented way (no additional steps such as
      code generation is required)

    - object-oriented programing and feel - using classes, objects and references
      instead of relations, its columns, primary and foreign keys

    - object-oriented database operations:
        - add, update, delete
        - get and reload
        - easy object finding with support for SQL queries
        - association data load and reload

    - application class relationships:
        - one-to-one, one-to-many and many-to-many
        - uni-directional and bi-directional

    - application objects and association data cache integrated with Python
      garbage collector:
        - full - load all rows at once from relation
        - lazy - load one row from relation

    - configurable - connection string, DB API module, class relations, object
      and association data cache types, etc.

Requirements:
    - Python 2.4
    - Python DB API 2.0 module with ``format'' and ``pyformat'' parameter style
      support (tested with U{psycopg 2.0<http://initd.org/software/psycopg>})
    - RDBMS (tested with U{PostgreSQL 8.0<http://www.postgresql.org>})

This is free software distributed under U{GNU Lesser General Public
License<http://www.gnu.org/licenses/lgpl.html>}. Download it from
U{project's page<http://savannah.nongnu.org/projects/bazaar/>}
on U{Savannah<http://savannah.nongnu.org>}.

Bazaar ORM is easy to use, but is designed for people who know both
object-oriented and relational technologies, their advantages,
disadvantages and differences between them (U{``The Object-Relational
Impedance Mismatch''<http://www.agiledata.org/essays/impedancemismatch.html>}
reading is recommended).

Using the layer
===============

Creating application classes
----------------------------

Let's consider following diagram::

    Order < 1 ---- * > OrderItem
    OrderItem | * ---- 1 > Article

There are three classes and two associations. Both relationships are one to
many associations, but first one is bi-directional and second is
uni-directional.

Class definition (more about class and relationships defining can be
found in L{bazaar.conf} module documentation) should be like::

    # import bazaar module used to create classes
    >>> import bazaar.conf

    # create class for articles
    >>> Article = bazaar.conf.Persistence('Article', 'article', globals())

    # add class attributes and relation columns
    # class attribute name is the same as relation column name
    >>> Article.addColumn('name')
    >>> Article.addColumn('price')

    # create order and order items classes
    # class names are different than database relation names
    >>> Order = bazaar.conf.Persistence('Order', 'order', globals())
    >>> OrderItem = bazaar.conf.Persistence('OrderItem', 'order_item',
    ...     globals())

    >>> Order.addColumn('no')                          # order number
    >>> Order.addColumn('finished', default = False)   # is order completed
    >>> OrderItem.addColumn('pos')                     # order item position
    >>> OrderItem.addColumn('quantity')                # article quantity

    # define bi-directional association between Order and OrderItem classes
    #
    # from OrderItem perspective
    # attribute name: order
    # relation column name: order_fkey
    # referenced object's class: Order
    # referenced object's class attribute name: items
    >>> OrderItem.addColumn('order', 'order_fkey', Order, vattr = 'items')

    # from Order perspective
    # attribute name: items
    # referenced object's class: OrderItem
    # referenced relation column name: order_fkey
    # referenced object's class attribute name: order
    >>> Order.addColumn('items', vcls = OrderItem, vcol = 'order_fkey',
    ...     vattr = 'order')

    # define uni-directional association between OrderItem and Article classes
    # 
    # attribute name: article
    # relation column name: article_fkey
    # referenced object's class: Article
    >>> OrderItem.addColumn('article', 'article_fkey', Article)

Now, SQL schema can be created::

    # primary key values generator
    create sequence order_seq;
    create table "order" (
        # every application object is identified with uuid attribute
        uuid      integer,
        no           integer not null unique,
        finished     boolean not null,
        primary key (uuid)
    );

    create sequence article_seq;
    create table article (
        uuid      integer,
        name         varchar(20) not null,
        price        numeric(10,2) not null,
        unique (name),
        primary key (uuid)
    );

    create sequence order_item_seq;
    create table order_item (
        uuid      integer,
        order_fkey   integer,
        pos          integer not null,
        article_fkey integer not null,
        quantity     numeric(10,3) not null,
        primary key (uuid),
        unique (order_fkey, pos),

        # association between Order and OrderItem
        foreign key (order_fkey) references "order"(uuid),

        # association between OrderItem and Article
        foreign key (article_fkey) references article(uuid)
    );

Application code
----------------

Application must import Bazaar ORM core module::

    >>> import bazaar.core
    >>> import psycopg

DB API module is imported, too. However, it is not obligatory because it can
be specified in config file, see L{bazaar.config} module documentation for
details.

Create Bazaar ORM layer instance. There are several parameters
(L{bazaar.core.Bazaar}), but for this example the list of application
classes, DB API module are specified:: #fimxe

    >>> bzr = bazaar.core.Bazaar((Article, Order, OrderItem), \
            dbmod = psycopg, seqpattern = "select nextval('%s')")

Connect to database::

    >>> bzr.connectDB('dbname = bazaar')

Connection string is standard database source name (dsn) described in DB
API 2.0 specification. Connection can be established with
L{bazaar.core.Bazaar} class constructor, too.

Create application object::

    >>> apple = Article()
    >>> apple.name = 'apple'
    >>> apple.price = 2.33
    >>> print apple.price
    2.33

    
Object constructor can initialize object attributes::

    >>> oi1 = OrderItem(pos = 1, quantity = 10)
    >>> oi1.article = apple
    >>> print oi1.article.name, oi1.pos, oi1.quantity
    apple 1 10

    >>> peach = Article()
    >>> peach.name = 'peach'
    >>> peach.price = 2.34

    >>> oi2 = OrderItem(article = peach)
    >>> oi2.pos = 2
    >>> oi2.quantity = 40
    >>> print oi2.article.name, oi2.pos, oi2.quantity
    peach 2 40

Create new order::

    >>> ord = Order(no = 10000)


Append order items to order. It can be made in two ways
(it is bi-directional relationship)::

    >>> ord.items.append(oi1)     # append item to order
    >>> oi2.order = ord           # set order of an item
    >>> print [item.article.name for item in ord.items]
    ['apple', 'peach']


Finally, add created objects data into database and update association
between order and its items::

    >>> bzr.add(apple)
    >>> bzr.add(peach)
    >>> bzr.add(oi1)
    >>> bzr.add(oi2)
    >>> bzr.add(ord)

    >>> ord.items.update()

Objects can be updated and deleted, too (L{bazaar.core.Bazaar}).


Now, let's play with some objects. Remove second order item from order
number 10000::

    >>> del ord.items[oi2]
    >>> print oi2 in ord.items
    False
    >>> print [item.article.name for item in ord.items]
    ['apple']

And update association::

    >>> ord.items.update()

Add second order item again::

    >>> ord.items.append(oi2)
    >>> print oi2 in ord.items
    True
    >>> ord.items.update()

Change apple price::

    >>> apple.price = 2.00

And update database data::

    >>> bzr.update(apple)

Print all orders::

    >>> print [ord.no for ord in bzr.getObjects(Order)]    # doctest: +ELLIPSIS
    [...]


Find order number 1::

    >>> ord = bzr.find(Order, {'no': 1}).next()
    >>> print ord.no
    1

Find order items for article "apple"::

    >>> oi = bzr.find(OrderItem,  {'article': apple}).next()
    >>> print oi.article.name, oi.article.price, oi.quantity
    apple 2.0 10

Finally, commit or rollback transaction::

    >>> bzr.rollback()
"""
# @todo:
# Bazaar supports GUI development with set of powerful widgets designed
# to simplify development of presentation, manipulation and
# data searching.

class Log(object):
    """
    Utility class to deffer creation of loggers (of logging package).

    Usage::

        log = Log('bazaar.core') # log is Log instance
        log.debug()              # log is logging.Logger instance

    @ivar logger: Logger name.
    """
    def __init__(self, logger):
        """
        Create log utility class
        """
        self.logger = logger


    def __getattr__(self, attr):
        """
        Replace log utility instance with real logger from logging package.
        """
        import logging
        import sys
        log = logging.getLogger(self.logger)
        # find modules and utility instance names
        for mod in sys.modules.itervalues():
            if mod is not None:
                # get module variable names, which refer to the instance of
                # current Log class instance, so they can be replaced by
                # real logger
                modvars = [name for name, var in mod.__dict__.items()
                            if var is self]

                if modvars:
                    break

        # replace utility instances
        for name in modvars:
            setattr(mod, name, log)

        # return requested logger's method/attribute
        return getattr(log, attr)

        # this method should not be called again for object self, now
