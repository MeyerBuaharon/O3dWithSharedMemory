from multiprocessing import Pool, Manager
from time import sleep
import threading
from random import random

gas_list = [1,2,3,4,5,6,7,8,9,10]

def main_reader(sen, rqu):
    output = "%d/%f" % (sen, random())
    rqu.put(output)


def all_processes(rq):
    p = Pool(len(gas_list) + 1)
    while True:
        for sen in gas_list:
            p.apply_async(main_reader, args=(sen, rq))

        sleep(1)

m = Manager()
q = m.Queue()
t = threading.Thread(target=all_processes, args=(q,))
t.daemon = True
t.start()

while True:
    r = q.get()
    print (r)
