import time
import MySQLdb

class Job(object):
    table = "queue"
    def __init__(self, j_id, order_id, printer_id=None, state=0, fails=0, created_at=time.strftime('%Y-%m-%d %H:%M:%S')):
        self.id = j_id
        self.order_id = order_id
        if printer_id:
            self.printer_id = printer_id
        else:
            self.printer_id = 'NULL'
        self.state = state
        self.fails = fails
        self.created_at = str(created_at)

    def save(self, database):
        query = "UPDATE {0} SET printer_id='{1}', state='{2}', fails='{3}', updated_at='{4}' WHERE id={5}".format(Job.table, self.printer_id, self.state, self.fails, time.strftime('%Y-%m-%d %H:%M:%S'), self.id)
        database.update(query)

if __name__ == '__main__':
    import database
    j = Job(1, 1, 3,1)
    j.save(database.DataBase('control', 'controlhack', '10.4.180.201', "imp3d"))
