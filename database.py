import MySQLdb

class DataBase(object):
    def __init__(self, user, passwd, host, db):
        self._user = user
        self._passwd = passwd
        self._host = host
        self._db = db
        self.connection = MySQLdb.connect(user=self._user, passwd=self._passwd, host=self._host, db=self._db)
        self.cursor = self.connection.cursor()

    def read(self, query):
        try:
            self.cursor.execute(query)
            table = self.cursor.fetchall()
            table_l = []
            for row in table:
                table_l += [list(row)]
            return table_l
        except Exception as exception:
            return exception

    def write(self, query):
        try:
            try:
                self.cursor.execute(query)
                self.connection.commit()
            except:
                self.connection.rollback()
            return True
        except Exception as exception:
            return exception

    def update(self, query):
        return self.write(query)
