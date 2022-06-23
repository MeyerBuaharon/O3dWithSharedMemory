import numpy as np
import open3d as o3d
import open3d.visualization.gui as gui
import open3d.visualization.rendering as rendering
import time
import threading

from open3d.cuda.pybind.core import Tensor


class VideoWindow:

    def __init__(self):
        self.pcdA = o3d.t.geometry.PointCloud()
        self.pcdB = o3d.t.geometry.PointCloud()

        self.window = gui.Application.instance.create_window("Open3D - Video Example", 1000, 500)

        self.widget3d = gui.SceneWidget()
        self.widget3d.scene = rendering.Open3DScene(self.window.renderer)
        self.window.add_child(self.widget3d)

        self.is_done = False
        threading.Thread(target=self._update_thread).start()

    def get_ply_from_shared_mem(self, pcd):
        data_lines = np.random.randint(100, 100000)
        buff_x2 = np.random.randint(-10000, 10000, size=data_lines)
        buff_y2 = np.random.randint(-1000, 1000, size=data_lines)
        buff_z2 = np.random.randint(-10, 10, size=data_lines)
        buff_r2 = np.random.randint(254, 255, size=data_lines)
        buff_g2 = np.random.randint(0, 1, size=data_lines)
        buff_b2 = np.random.randint(0, 1, size=data_lines)

        self.load_point_cloud(data_lines, buff_x2, buff_y2, buff_z2, buff_r2, buff_g2, buff_b2, pcd)

    def load_point_cloud(self, data_lines, buff_x_breakdown, buff_y_breakdown, buff_z_breakdown,
                         buff_r_breakdown, buff_g_breakdown, buff_b_breakdown, pcd):

        xyz = np.zeros((data_lines, 3))
        colors = np.zeros((data_lines, 3))

        xyz[:, 0] = buff_x_breakdown
        xyz[:, 1] = buff_y_breakdown
        xyz[:, 2] = buff_z_breakdown

        colors[:, 0] = buff_r_breakdown
        colors[:, 1] = buff_g_breakdown
        colors[:, 2] = buff_b_breakdown

        xyz = Tensor(xyz, dtype=o3d.core.float32)
        colors = Tensor(colors, dtype=o3d.core.float32)

        tempPcd = o3d.t.geometry.PointCloud({
            'positions': xyz,
            'colors': colors / 255,
        })

        if pcd == 'A':
            self.pcdA = tempPcd
        if pcd == 'B':
            self.pcdB = tempPcd

    def get_ply_a(self):
        idx = 0
        while True:
            time.sleep(1 / 10000)
            if True:
                try:
                    idx +=1
                    self.is_a_ready = False

                    self.get_ply_from_shared_mem('A')
                    self.widget3d.scene.scene.update_geometry('frameA', self.pcdA,
                                                              rendering.Scene.UPDATE_POINTS_FLAG |
                                                              rendering.Scene.UPDATE_COLORS_FLAG)
                    self.is_a_ready = True

                except:
                    print('cant get pcd A')

    def get_ply_b(self):
        idx = 0
        while True:
            idx += 1
            time.sleep(1 / 10000)
            if True:
                try:
                    self.is_b_ready = False

                    self.get_ply_from_shared_mem('B')
                    self.widget3d.scene.scene.update_geometry('frameB', self.pcdB,
                                                              rendering.Scene.UPDATE_POINTS_FLAG |
                                                              rendering.Scene.UPDATE_COLORS_FLAG)
                    self.is_b_ready = True


                except:
                    print('cant get pcd B')
                    pass

    def _update_thread(self):
        pcd_placeholder = o3d.t.geometry.PointCloud(Tensor(np.zeros((1000000, 3), dtype=np.float32)))
        pcd_placeholder.point['colors'] = Tensor(np.zeros((1000000, 3), dtype=np.float32))
        self.widget3d.scene.scene.add_geometry('frameA', pcd_placeholder, rendering.MaterialRecord())
        self.widget3d.scene.scene.add_geometry('frameB', pcd_placeholder, rendering.MaterialRecord())

        threading.Thread(target=self.get_ply_a).start()
        threading.Thread(target=self.get_ply_b).start()

        while not self.is_done:
            time.sleep(1 /10000)
            # if self.is_a_ready and self.is_b_ready:
            self.window.post_redraw()


def main():
    gui.Application.instance.initialize()
    win = VideoWindow()
    gui.Application.instance.run()


if __name__ == "__main__":
    main()
