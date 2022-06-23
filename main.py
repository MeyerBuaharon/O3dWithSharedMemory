import threading
import time
from functools import partial

import numpy as np
import requests
from open3d.cuda.pybind.utility import Vector3dVector
from open3d.visualization import gui, rendering

from configurations import Configurations

import shared_mem
import open3d as o3d
import open3d.core as o3c

pcdA = o3d.t.geometry.PointCloud()
pcdB = o3d.t.geometry.PointCloud()

configuration = Configurations()

current_camera_pov = configuration.get_camera_pov('reset')
prev_front = current_camera_pov['front']
prev_lookat = current_camera_pov['lookat']
prev_up = current_camera_pov['up']
prev_zoom = current_camera_pov['zoom']

should_animate = False
should_speed = True
animation_id = 0


def reset(preset_name, vis):
    global should_animate, current_camera_pov, animation_id, prev_zoom, prev_up, prev_lookat, prev_front

    current_camera_pov = configuration.get_camera_pov(preset_name)
    prev_front = current_camera_pov['front']
    prev_lookat = current_camera_pov['lookat']
    prev_up = current_camera_pov['up']
    prev_zoom = current_camera_pov['zoom']

    view_ctl = vis.get_view_control()

    view_ctl.set_front(prev_front)
    view_ctl.set_lookat(prev_lookat)
    view_ctl.set_up(prev_up)
    view_ctl.set_zoom(prev_zoom)


def animate(preset_name, vis):
    global should_animate, current_camera_pov, animation_id
    should_animate = True
    animation_id = 0

    if should_animate:
        current_camera_pov = configuration.get_camera_pov(preset_name)


def mirror_speed(vis):
    global should_speed
    host = "http://localhost:8088"
    should_speed = not should_speed
    speed = 1
    if should_speed:
        speed = 2

    # Todo: get command list to mirror speed
    try:
        command = f'scan M {122 / speed}'
        print(command)

        sensor_name = 'Left'
        response = requests.post(f"{host}/sendCommandViaCOM?sensorName=${sensor_name}&cmd=${command}",
                                 auth=('user1', 'user1Pass'))
        print(response)
        sensor_name = 'Right'
        response = requests.get(f"{host}/sendCommandViaCOM?sensorName=${sensor_name}&cmd=${command}",
                                auth=('user1', 'user1Pass'))
        print(response)
    except:
        print("Error changing mirror speed")


def mock_pcd(pcd):
    global pcdA,pcdB
    data_lines = 90000
    buff_x2 = np.random.randint(-1000, 1000, size=data_lines).tobytes()
    buff_y2 = np.random.randint(-1000, 1000, size=data_lines).tobytes()  # np.full((1, data_lines), 20).tobytes()
    buff_z2 = np.random.randint(-1000, 1000, size=data_lines).tobytes()  # np.full((1, data_lines), 30).tobytes()
    buff_r2 = np.random.randint(-100, 100, size=data_lines).tobytes()  # np.full((1, data_lines), 0).tobytes()
    buff_g2 = np.random.randint(-100, 100, size=data_lines).tobytes()  # np.full((1, data_lines), 255).tobytes()
    buff_b2 = np.random.randint(-100, 100, size=data_lines).tobytes()  # np.full((1, data_lines), 0).tobytes()
    xyz = np.zeros((data_lines, 3))
    colors = np.zeros((data_lines, 3))

    xyz[:, 0] = np.frombuffer(buff_x2, dtype=np.float32, count=data_lines)
    xyz[:, 1] = np.frombuffer(buff_y2, dtype=np.float32, count=data_lines)
    xyz[:, 2] = np.frombuffer(buff_z2, dtype=np.float32, count=data_lines)

    colors[:, 0] = np.frombuffer(buff_r2, dtype=np.ubyte, count=data_lines)
    colors[:, 1] = np.frombuffer(buff_g2, dtype=np.ubyte, count=data_lines)
    colors[:, 2] = np.frombuffer(buff_b2, dtype=np.ubyte, count=data_lines)

    pcd_placeholder = o3d.t.geometry.PointCloud(o3c.Tensor(np.zeros((data_lines, 3), dtype=np.float32)))
    pcd_placeholder.point['positions'] = o3c.Tensor(xyz, dtype=o3d.core.float32)
    pcd_placeholder.point['colors'] = o3c.Tensor(colors / 255.0, dtype=o3d.core.float32)

    if pcd == 'A':
        pcdA.point['positions'] = pcd_placeholder.point['positions']
        pcdA.point['colors'] = pcd_placeholder.point['colors']

    if pcd == 'B':
        pcdB.point['positions'] = pcd_placeholder.point['positions']
        pcdB.point['colors'] = pcd_placeholder.point['colors']


def build_pcd(my_shm, pcd):
    global pcdA, pcdB
    buf = my_shm.shm.read(4, 5)
    data_lines = int.from_bytes(buf, "little")
    xyz = np.zeros((data_lines, 3))
    colors = np.zeros((data_lines, 3))

    # read all data
    buff_x2 = my_shm.shm_x.read(4 * data_lines, 0)
    buff_y2 = my_shm.shm_y.read(4 * data_lines, 0)
    buff_z2 = my_shm.shm_z.read(4 * data_lines, 0)
    buff_r2 = my_shm.shm_r.read(data_lines, 0)
    buff_g2 = my_shm.shm_g.read(data_lines, 0)
    buff_b2 = my_shm.shm_b.read(data_lines, 0)

    xyz[:, 0] = np.frombuffer(buff_x2, dtype=np.float32, count=data_lines)
    xyz[:, 1] = np.frombuffer(buff_y2, dtype=np.float32, count=data_lines)
    xyz[:, 2] = np.frombuffer(buff_z2, dtype=np.float32, count=data_lines)

    colors[:, 0] = np.frombuffer(buff_r2, dtype=np.ubyte, count=data_lines)
    colors[:, 1] = np.frombuffer(buff_g2, dtype=np.ubyte, count=data_lines)
    colors[:, 2] = np.frombuffer(buff_b2, dtype=np.ubyte, count=data_lines)

    if pcd == 'A':
        pcdA.points = Vector3dVector(xyz)
        pcdA.colors = Vector3dVector(colors / 255.0)

    if pcd == 'B':
        pcdB.points = Vector3dVector(xyz)
        pcdB.colors = Vector3dVector(colors / 255.0)


def run():
    global pcdA
    fps_idx = 0
    fps_interval_len = 30
    start = time.time()

    while True:
        time.sleep(0.01)

        widget3d.scene.scene.clear_geometry()
        fps_idx += 1
        mock_pcd('A')
        update_flags = (rendering.Scene.UPDATE_POINTS_FLAG |
                        rendering.Scene.UPDATE_COLORS_FLAG |
                        rendering.Scene.UPDATE_NORMALS_FLAG)
        widget3d.scene.scene.add_geometry('points', pcdA, rendering.MaterialRecord())
        if fps_idx % fps_interval_len == 0:
            end = time.time()
            elapsed = end - start
            start = time.time()
            fps_idx = 0
            print(fps_interval_len / elapsed)


if __name__ == '__main__':
    # shm1 = shared_mem.SharedMemory(1)
    # shm2 = shared_mem.SharedMemory(2)


    vis = o3d.visualization.VisualizerWithKeyCallback()
    window = vis.create_window()

    vis.get_render_option().background_color = [0.75, 0.75, 0.75]
    vis.get_render_option().mesh_show_back_face = True
    vis.get_render_option().point_size = 1
    # build_pcd(shm1, 'A')
    # build_pcd(shm2, 'B')
    pcdA = o3d.io.read_point_cloud('./3.ply')
    pcdB = o3d.io.read_point_cloud('./4.ply')
    vis.add_geometry(pcdA)
    vis.add_geometry(pcdB)
    view_ctl = vis.get_view_control()

    view_ctl.set_front(prev_front)
    view_ctl.set_lookat(prev_lookat)
    view_ctl.set_up(prev_up)
    view_ctl.set_zoom(prev_zoom)
    ### Key Binds: ####

    vis.register_key_callback(ord("M"), partial(mirror_speed))

    vis.register_key_callback(ord("R"), partial(reset, 'reset'))

    vis.register_key_callback(ord("0"), partial(animate, 'front 0'))
    vis.register_key_callback(ord("9"), partial(animate, 'front 10'))
    vis.register_key_callback(ord("8"), partial(animate, 'eagle 20'))
    vis.register_key_callback(ord("7"), partial(animate, 'bird eye'))
    vis.register_key_callback(ord("6"), partial(animate, 'bird eye 2'))
    vis.register_key_callback(ord("5"), partial(animate, 'zoom in'))

    # native_ready_flag = bool(int.from_bytes(shm1.shm.read(1, 0), "little"))
    # native_ready_flag2 = bool(int.from_bytes(shm2.shm.read(1, 0), "little"))
    #
    # if native_ready_flag:
    #     shm1.shm.write(shm1.byte_false, 0)
    #
    # if native_ready_flag2:
    #     shm2.shm.write(shm2.byte_false, 0)
    #
    # build_pcd(shm1, 'A')
    # build_pcd(shm2, 'B')

    vis.update_geometry(pcdA)
    vis.update_geometry(pcdB)

    if should_animate:
        animation_id += 1
        current_front = current_camera_pov['front']
        current_lookat = current_camera_pov['lookat']
        current_up = current_camera_pov['up']
        current_zoom = current_camera_pov['zoom']

        diff_front = prev_front + (current_front - prev_front) * (1 + animation_id) / 300
        diff_lookat = prev_lookat + (current_lookat - prev_lookat) * (1 + animation_id) / 300
        diff_up = prev_up + (current_up - prev_up) * (1 + animation_id) / 300
        diff_zoom = prev_zoom + (current_zoom - prev_zoom) * (1 + animation_id) / 300
        view_ctl = vis.get_view_control()

        view_ctl.set_front(diff_front)
        view_ctl.set_lookat(diff_lookat)
        view_ctl.set_up(diff_up)
        view_ctl.set_zoom(diff_zoom)
        animation_id += 1
        if animation_id >= 300:
            should_animate = False
            prev_front = current_front
            prev_up = current_up
            prev_lookat = current_lookat
            prev_zoom = current_zoom

    vis.poll_events()
    vis.update_renderer()
    vis.run()