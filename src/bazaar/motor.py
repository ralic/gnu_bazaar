# $Id: motor.py,v 1.2 2003/07/10 23:20:03 wrobell Exp $

from __future__ import generators
import logging

log = logging.getLogger('bazaar.motor')

"""
<s>Database access objects.</s>
<p>
</p>
"""

class Convertor:
    """
    <s>Database data convertor.</s>
    """
    def __init__(self, cls, mtr):
        """
        """
        self.queries = {}
        self.cls = cls
        self.motor = mtr

        self.columns = []
        for col in self.cls.columns.values():
            self.columns.append(col.name)

        # prepare quries
        self.queries[self.getObjects] = 'select %s from %s' \
            % (', '.join(self.columns), self.cls.relation)


    def getObjects(self):
        """
        <s>Load objects from database.</s>
        """
        for data in self.motor.getData(self.queries[self.getObjects], self.columns):
            obj = self.cls(data)   # create object instance
            yield obj



class Motor:
    """
    <s>Database access object.</s>
    """
    def __init__(self, db_module):
        """
        <s>Initialize database access object.</s>
        """
        self.db_module = db_module
        self.db_conn = None
        self.dbc = None
        log.info('Motor object initialized')


    def connectDB(self, dsn):
        """
        <s>Connect with database.</s>
        
        <attr name = 'dsn'>Data source name.</attr>

        <see>
            <r method = 'closeDBConn'>
        </see>
        """
        self.db_conn = self.db_module.connect(dsn)
        self.dbc = self.db_conn.cursor()
        if __debug__: log.debug('connected to database with dsn "%s"' % dsn)


    def closeDBConn(self):
        """
        <s>Close database connection.</s>

        <see>
            <r method = 'connectDB'>
        </see>
        """
        self.db_conn.close()
        self.db_conn = None
        self.dbc = None
        if __debug__: log.debug('close database connection')


    def getData(self, query, cols):
        """
        <s>Get list of rows from database.</s>
        <p>
            Method returns dictionary per databse relation row. The
            dictionary keys are relation column names and dictionary values
            are column values for the relation row.
        </p>

        <attr name = 'query'>Database SQL query.</s>
        <attr name = 'cols'>List of relation columns.</s>
        """
        if __debug__: log.debug('query "%s": executing' % query)

        self.dbc.execute(query)

        if __debug__: log.debug('query "%s": executed, rows = %d' % (query, self.dbc.rowcount))

        iter = range(len(cols))
        row = self.dbc.fetchone()
        while row:
            data = {}

            for i in iter: data[cols[i]] = row[i]
            yield data

            row = self.dbc.fetchone()

        if __debug__: log.debug('query "%s": got all data, len = %d' % (query, self.dbc.rowcount))
