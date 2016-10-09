import requests
import time
import urllib2
import urllib
import os

class Printer(object):
    api_key = "7CFB43BDCD8943F5A4A624050DE25AB8"
    f_api_key = "1029384756"
    f_host = "10.4.180.28"
    table = "printers"
    def __init__(self,p_id,host,name="",state=0,created_at=time.strftime('%Y-%m-%d %H:%M:%S'), updated_at=time.strftime('%Y-%m-%d %H:%M:%S')):
        self.id = p_id
        self.host = host
        self.name = name
        self.state = state
        self._unchange_state = False
        self.tool0_temp = 0
        self.bed_temp = 0
        self.progress = 0
        self.elapsed_time = 0
        self.aprox_time = 0
        self.estimated_time = 0
        self._consecutive_errors = 0
        self._consecutive_errors_int = False
        self._last_state = self.state
        self.created_at = str(created_at)

    def check_connection(self):
        """
        0 - Not online
        1 - Bad API key
        2 - Bad response
        3 - OK
        """
        try:
            resp = requests.get('http://{0}/api/version?apikey={1}'.format(self.host, Printer.api_key))
        except requests.exceptions.ConnectionError:
            return 0
        if resp.status_code == 401:
            return 1
        elif resp.status_code != 200:
            return 2
        else:
            return 3

    def refresh_data(self):
        if self.state != 5 and self.check_connection() == 3:
            resp = requests.get('http://{0}/api/printer?apikey={1}&exclude=history,sd'.format(self.host, Printer.api_key))
            if resp.status_code == 409:
                if not self._unchange_state:
                    if self.state == 2:
                        self.state = 4
                        self.tool0_temp = 0
                        self.bed_temp = 0
                        self.aprox_time = 0
                        self.estimated_time = 0
                        self._unchange_state = True
                    else:
                        self.state = 0
            elif resp.status_code == 200:
                data = resp.json()
                temps = data['temperature']
                state_flags = data['state']['flags']
                self.tool0_temp = temps['tool0']['actual']
                self.bed_temp = temps['bed']['actual']
                if not self._unchange_state:
                    if state_flags['operational'] and state_flags['ready']:
                        if state_flags['printing'] or state_flags['paused']:
                            self.state = 2
                            job_resp = requests.get('http://{0}/api/job?apikey={1}'.format(self.host, Printer.api_key))
                            if job_resp.status_code == 200:
                                job_data = job_resp.json()
                                progress_data = job_data['progress']
                                self.progress = round(progress_data['completion'], 2)
                                self.elapsed_time = progress_data['printTime']
                                self.aprox_time = job_data['job']['estimatedPrintTime']
                                self.estimated_time = progress_data['printTimeLeft']
                        else:
                            if self.state == 2 and round(self.progress,0) == 100:
                                self.state = 3
                                self.estimated_time = 0
                                self._unchange_state = True
                            elif self.state == 2 and self.progress != 100:
                                self.state = 4
                                self._unchange_state = True
                            else:
                                self.state = 1
                                self.progress = 0
                    elif state_flags['error']:
                        self.state = 4
                        self.tool0_temp = 0
                        self.bed_temp = 0
                        self._unchange_state = True

    def set_ready(self):
        self.state = 1
        if self._unchange_state:
            self._unchange_state = False

    def cancel_print(self):
        command = {'command':'cancel'}
        resp = requests.post('http://{0}/api/job?apikey={1}'.format(self.host, Printer.api_key),json=command)

    def start_print(self, f_name):
        while True:
            try:
                file_complete = "./tmp/{}.gcode".format(f_name)
                print "http://{0}/api/file/{1}.gcode/{2}".format(Printer.f_host, f_name, Printer.f_api_key)
                file_d = urllib.URLopener()
                file_d.retrieve("http://{0}/api/file/{1}.gcode/{2}".format(Printer.f_host, f_name, Printer.f_api_key), file_complete)
                f = open(file_complete, "r")
                f_data = f.read()
                #print f_data
                resp = requests.post('http://{0}/api/files/local?apikey={1}'.format(self.host, Printer.api_key), files={"file" : ("{}.gcode".format(f_name), f_data), "print" : (None, "true")})
                while resp.status_code != 201:
                    if resp.status_code in (400,404,409,415,500):
                        self.state = 4
                        self._unchange_state = True
                        break
                os.system("rm -f {}".format(file_complete))
                break
            except:
                pass

    def save(self, database):
        if not self._consecutive_errors_int:
            query = "SELECT consecutive_errors FROM {0} WHERE id={1}".format(Printer.table, self.id)
            r = database.read(query)
            if r != []:
                self._consecutive_errors = r[0][0]
            else:
                if self.state == 4:
                    self._consecutive_errors = 1
                else:
                    self._consecutive_errors = 0
                query = "INSERT INTO {0} (id, host, name, state, tool0_temp, bed_temp, progress, elapsed_time, aprox_time, estimated_time, consecutive_errors, created_at, updated_at) VALUES ('{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}', '{9}', '{10}', '{11}', '{12}', '{13}')".format(Printer.table, self.id, self.host, self.name, self.state, self.tool0_temp, self.bed_temp, self.progress, self.elapsed_time, self.aprox_time, self.estimated_time, consecutive_errors, self.created_at, time.strftime('%Y-%m-%d %H:%M:%S'))
                database.write(query)
            query = "SELECT state FROM {0} WHERE id={1}".format(Printer.table, self.id)
            r = database.read(query)[0][0]
            if r == 5:
                self.state = 5
                self._consecutive_errors = 0
            self._consecutive_errors_int = True
        else:
            query = "SELECT state FROM {0} WHERE id={1}".format(Printer.table, self.id)
            r = database.read(query)[0][0]
            if self._last_state == self.state and r != self.state:
                self.state = r
                if self.state == 1 or self.state == 4:
                    self.progress = 0
                    if self.state == 1:
                        self._unchange_state = False
                if self._last_state == 2 and self.state == 4:
                    self.cancel_print()
            if self.state == 4 and self._last_state != self.state:
                self._consecutive_errors += 1
                self._unchange_state = True
            elif self._last_state == 3 and self.state == 1:
                self._consecutive_errors = 0
        if self._consecutive_errors >= 3:
            self.state = 5
            self.progress = 0
            self._consecutive_errors = 0
            self._unchange_state = True
        self._last_state = self.state
        if self.state == 5:
            self._consecutive_errors = 0
            self.progress = 0
        query = "UPDATE {0} SET host='{1}', state='{2}', tool0_temp='{3}', bed_temp='{4}', progress='{5}', elapsed_time='{6}', aprox_time='{7}', estimated_time='{8}', consecutive_errors='{9}', updated_at='{10}' WHERE id='{11}'".format(Printer.table, self.host, self.state, self.tool0_temp, self.bed_temp, self.progress, self.elapsed_time, self.aprox_time, self.estimated_time, self._consecutive_errors, time.strftime('%Y-%m-%d %H:%M:%S'), self.id)
        database.update(query)


if __name__ == '__main__':
    import time
    import database

    db = database.DataBase('control', 'controlhack', '10.4.180.28', "imp3d")
    p = Printer(3,"10.193.48.155:5000",'IMPRESORA3')
    i = 0
    while True:
        p.refresh_data()
        print p.state
        print p._last_state
        print p.tool0_temp
        print p.bed_temp
        print p.progress
        print p.elapsed_time
        print p.aprox_time
        print p.estimated_time
        print "------"
        p.save(db)
        time.sleep(1)
