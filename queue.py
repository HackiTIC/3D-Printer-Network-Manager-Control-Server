import job
import printer
import time

class Queue(object):
    q_table = "queue"
    p_table = "printers"
    o_table = "orders"
    def __init__(self, database):
        self._database = database
        self._get_all_printers()

    def _get_all_printers(self):
        query = "SELECT id,host FROM {}".format(Queue.p_table)
        self.printer_ids = dict()
        for p_id,host in self._database.read(query):
            p = printer.Printer(p_id,host)
            p.refresh_data()
            self.printer_ids[int(p_id)] = p

    def _update_printer_dict(self):
        query = "SELECT id,host FROM {}".format(Queue.p_table)
        self.printer_ids = dict()
        existing_ids = self.printer_ids.keys()
        for p_id,host in self._database.read(query):
            if p_id not in existing_ids:
                p = printer.Printer(p_id,host)
                p.refresh_data()
                self.printer_ids[int(p_id)] = p

    def get_last_queue(self):
        query = "SELECT * FROM {}".format(Queue.q_table)
        self.queue_dict_id = dict()
        self.queue_dict_pid = dict()
        for db_job in self._database.read(query):
            if db_job[2] == 'NULL':
                p_id = None
            else:
                p_id = db_job[2]
            j = job.Job(db_job[0],db_job[1],p_id,db_job[3],db_job[4],str(db_job[5]))
            self.queue_dict_id[int(db_job[0])] = j
            if p_id:
                self.queue_dict_pid[int(p_id)] = j

    def get_printing_jobs(self):
        self.printing_jobs_p_ids = dict()
        for job in self.queue_dict_id.values():
            if job.state == 1:
                self.printing_jobs_p_ids[job.printer_id] = job

    def get_ready_jobs(self):
        self.ready_jobs = dict()
        for job in self.queue_dict_id.values():
            print "job.printer_id ->",job.printer_id
            if job.state == 0 and job.printer_id == 'NULL':
                self.ready_jobs[int(job.id)] = job
        if self.ready_jobs == {}:
            self.ready_jobs_ids = []
        else:
            self.ready_jobs_ids = sorted(self.ready_jobs)

    def get_ready_printers(self):
        self.ready_printers = list()
        for p in self.printer_ids.values():
            if p.state == 1:
                self.ready_printers += [p]

    def rearm_failed_printings(self):
        for job_p_id in self.printing_jobs_p_ids.keys():
            job = self.printing_jobs_p_ids[job_p_id]
            query = "SELECT state FROM {0} WHERE id={1}".format(Queue.p_table, job_p_id)
            p_state = self._database.read(query)[0][0]
            print p_state
            if p_state == 4 or p_state == 0 or p_state == 5:
                job.printer_id = 'NULL'
                job.fails += 1
                if job.fails > 2:
                    job.state = 3
                else:
                    job.state = 0
            job.save(self._database)

    def start_ready_jobs(self):
        i = 0
        for p in self.ready_printers:
            if i == len(self.ready_jobs):
                break
            job = self.ready_jobs[self.ready_jobs_ids[i]]
            job.printer_id = p.id
            job.state = 1
            query = "SELECT filename FROM {0} WHERE id={1}".format(Queue.o_table, job.order_id)
            f_name = ""
            print self._database.read(query)[0][0].split(".")[:-1]
            f_name = ".".join(self._database.read(query)[0][0].split(".")[:-1])
            p.start_print(f_name)
            #p.refresh_data()
            job.save(self._database)
            p.save(self._database)
            i+=1

    def queue_run(self):
        self.get_last_queue()
        self.get_printing_jobs()
        #self._update_printer_dict()
        self.rearm_failed_printings()
        self.get_last_queue()
        self.get_ready_jobs()
        self.get_ready_printers()
        self.start_ready_jobs()

    def refresh_printers(self):
        for p in self.printer_ids.values():
            p.refresh_data()
            p.save(self._database)

if __name__ == '__main__':
    import database
    j = Queue(database.DataBase('control', 'controlhack', '10.4.180.28', "imp3d"))
    while True:
        j.queue_run()
        j.refresh_printers()
        time.sleep(0.5)
