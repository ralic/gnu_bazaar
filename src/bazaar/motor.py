# $Id: motor.py,v 1.9 2003/08/25 19:01:06 wrobell Exp $
"""
Data convertor and database access objects.
"""

import logging

log = logging.getLogger('bazaar.motor')

class Convertor:
    """
    Data convertor.

    @ivar queries: Queries to modify data in database.
    @ivar cls: Application class, which objects are converted.
    @ivar motor: Database access object.
    @ivar columns: List of columns used with database queries.
    """
    def __init__(self, cls, mtr):
        """
        Create data convert object.
        """
        self.queries = {}
        self.cls = cls
        self.motor = mtr

        self.columns = [col.name for col in self.cls.columns.values()]

        #
        # set convert key method for single or multicolumn relation key;
        # convert key methods creates tupple from object key data
        #

        # multicolumn key method
        def getMKey(key):
            return key

        # single column key method
        def getKey(key):
            return (key, )

        if len(self.cls.key_columns) == 1:
            self.convertKey = getKey
        else:
            self.convertKey = getMKey

        #
        # prepare queries
        #
        self.queries[self.getObjects] = 'select %s from "%s"' \
            % (', '.join(['"%s"' % col for col in self.columns]), self.cls.relation)

        if __debug__: log.debug('get object query: "%s"' % self.queries[self.getObjects])

        self.queries[self.add] = 'insert into "%s" (%s) values (%s)' \
            % (self.cls.relation,
               ', '.join(['"%s"' % col for col in self.columns]),
               ', '.join(['%%(%s)s' % col for col in self.columns])
              )

        if __debug__: log.debug('add object query: "%s"' % self.queries[self.add])

        self.queries[self.update] = 'update "%s" set %s where %s' \
            % (self.cls.relation,
               ', '.join(['"%s" = %%s' % col for col in self.columns]),
               ' and '.join(['"%s" = %%s' % col for col in self.cls.key_columns])
              )
        if __debug__: log.debug('update object query: "%s"' % self.queries[self.update])

        self.queries[self.delete] = 'delete from "%s" where %s' \
            % (self.cls.relation,
               ' and '.join(['"%s" = %%s' % col for col in self.cls.key_columns])
              )
        if __debug__: log.debug('delete object query: "%s"' % self.queries[self.delete])


    def getObjects(self):
        """
        Load objects from database.
        """
        for data in self.motor.getData(self.queries[self.getObjects], self.columns):
            obj = self.cls(data)   # create object instance
            obj.key = obj.__class__.getKey(obj)

            yield obj


    def add(self, obj):
        """
        Add object to database.

        @param obj: Object to add.
        """
        self.motor.add(self.queries[self.add], obj.__dict__)
        obj.key = obj.__class__.getKey(obj)
 

    def update(self, obj):
        """
        Update object in database.

        @param obj: Object to update.
        """
        self.motor.update(self.queries[self.update], \
            [obj.__dict__[col] for col in self.columns], self.convertKey(obj.key))
        obj.key = obj.__class__.getKey(obj)


    def delete(self, obj):
        """
        Delete object from database.

        @param obj: Object to delete.
        """
        self.motor.delete(self.queries[self.delete], self.convertKey(obj.key))



class Motor:
    """
    Database access object.

    @ivar db_module: Python DB API module.
    @ivar db_conn: Python DB API connection object.
    @ivar dbc: Python DB API cursor object.
    """
    def __init__(self, db_module):
        """
        Initialize database access object.
        """
        self.db_module = db_module
        self.db_conn = None
        self.dbc = None
        log.info('Motor object initialized')


    def connectDB(self, dsn):
        """
        Connect with database.
        
        @param dsn: Data source name.

        @see: L{bazaar.motor.Motor.closeDBConn}
        """
        self.db_conn = self.db_module.connect(dsn)
        self.dbc = self.db_conn.cursor()
        if __debug__: log.debug('connected to database with dsn "%s"' % dsn)


    def closeDBConn(self):
        """
        Close database connection.

        @see: L{bazaar.motor.Motor.connectDB}
        """
        self.db_conn.close()
        self.db_conn = None
        self.dbc = None
        if __debug__: log.debug('close database connection')


    def getData(self, query, cols):
        """
        Get list of rows from database.

        Method returns dictionary per databse relation row. The
        dictionary keys are relation column names and dictionary values
        are column values for the relation row.

        @param query: Database SQL query.
        @param cols: List of relation columns.
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


    def add(self, query, data):
        """
        Insert row into database relation.

        @param query: SQL query.
        @param data: Row data to insert.
        """
        if __debug__: log.debug('query "%s", data = %s: executing' % (query, data))
        self.dbc.execute(query, data)
        if __debug__: log.debug('query "%s", data = %s: executed' % (query, data))


    def update(self, query, data, key):
        """
        Update row in database relation.

        @param query: SQL query.
        @param data: Tuple of new values for the row.
        @param key: Key of the row to update.
        """
        if __debug__: log.debug('query "%s", data = %s, key = %s: executing' % (query, data, key))
        self.dbc.execute(query, tuple(data) + tuple(key))
        if __debug__: log.debug('query "%s", data = %s, key = %s: executed' % (query, data, key))


    def delete(self, query, key):
        """
        Delete row from database relation.

        @param query: SQL query.
        @param key: Key of the row to delete.
        """
        if __debug__: log.debug('query "%s", key = %s: executing' % (query, key))
        self.dbc.execute(query, key)
        if __debug__: log.debug('query "%s", key = %s: executed' % (query, key))


    def commit(self):
        """
        Commit pending database transactions.
        """
        self.db_conn.commit()


    def rollback(self):
        """
        Rollback database transactions.
        """
        self.db_conn.rollback()
