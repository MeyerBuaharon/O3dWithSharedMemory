import array

import sysv_ipc as ipc
import warnings


class SharedMemory:

    def __init__(self, headunit):
        warnings.filterwarnings("ignore")
        path = "/tmp"

        self.byte_true = bytes([1])
        self.byte_false = bytes([0])

        if headunit == 1:
            route = 0x3110
        else:
            route = 0x3120

        # shared memory header
        key = ipc.ftok(path, route)
        self.shm = ipc.SharedMemory(key, 0, 0)
        self.shm.attach(0, 0)
        # shared memory X values
        key_x = ipc.ftok(path, route+1)
        self.shm_x = ipc.SharedMemory(key_x, 0, 0)
        self.shm_x.attach(0, 0)
        # shared memory Y values
        key_y = ipc.ftok(path, route+2)
        self.shm_y = ipc.SharedMemory(key_y, 0, 0)
        self.shm_y.attach(0, 0)
        # shared memory Z values
        key_z = ipc.ftok(path, route+3)
        self.shm_z = ipc.SharedMemory(key_z, 0, 0)
        self.shm_z.attach(0, 0)
        # shared memory R values
        key_r = ipc.ftok(path, route+4)
        self.shm_r = ipc.SharedMemory(key_r, 0, 0)
        self.shm_r.attach(0, 0)
        # shared memory G values
        key_g = ipc.ftok(path, route+5)
        self.shm_g = ipc.SharedMemory(key_g, 0, 0)
        self.shm_g.attach(0, 0)
        # shared memory B values
        key_b = ipc.ftok(path, route+6)
        self.shm_b = ipc.SharedMemory(key_b, 0, 0)
        self.shm_b.attach(0, 0)

        self.shm.write(self.byte_true, 0)
        print("shared Memory init")

    def clear_mem(self):
        clear_size = array.array('B', [0] * self.shm.size)

        self.shm.write(clear_size, 0)
        self.shm_r.write(clear_size, 0)
        self.shm_g.write(clear_size, 0)
        self.shm_b.write(clear_size, 0)
        self.shm_x.write(clear_size, 0)
        self.shm_y.write(clear_size, 0)
        self.shm_z.write(clear_size, 0)