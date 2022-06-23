import os, shutil, configparser

import numpy as np
from numpy import unique


class Configurations:

    def __init__(self):
        self.path = './configurations.ini'
        self.pcd_padding_x = 0
        self.pcd_padding_y = 0
        self.pcd_padding_z = 0
        self.pov_presets_names = set()

        file_exists = os.path.exists(self.path)
        self.cfgfile = open(self.path, 'a+')
        self.write_config = configparser.ConfigParser()

        if not file_exists:
            self.write_config.add_section('camera_pov_preset')
            self.write_config.add_section('pointcloud_padding')
            self.write_config.set('pointcloud_padding', 'x', '0')
            self.write_config.set('pointcloud_padding', 'y', '0')
            self.write_config.set('pointcloud_padding', 'z', '0')
            self.write_config.write(self.cfgfile)
            self.cfgfile.close()

        read_config = configparser.ConfigParser()
        read_config.read(self.path)

        pcd_padding = read_config['pointcloud_padding']

        self.pcd_padding_x = pcd_padding['x']
        self.pcd_padding_y = pcd_padding['y']
        self.pcd_padding_z = pcd_padding['z']
        self.get_pov_presets_names()

    def set_x_padding(self, value):
        self.pcd_padding_x = value
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(self.path)
        config.set('pointcloud_padding', 'x', str(value))
        with open(self.path, 'w') as configfile:
            config.write(configfile)

    def set_y_padding(self, value):
        self.pcd_padding_y = value
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(self.path)
        config.set('pointcloud_padding', 'y', str(value))
        with open(self.path, 'w') as configfile:
            config.write(configfile)

    def set_z_padding(self, value):
        self.pcd_padding_z = value
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(self.path)
        config.set('pointcloud_padding', 'z', str(value))
        with open(self.path, 'w') as configfile:
            config.write(configfile)

    def add_camera_pov(self,name, coords):
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(self.path)
        for key in coords.keys():
            config.set('camera_pov_preset', name+'.'+key, str(coords[key].vector_value))

        with open(self.path, 'w') as configfile:
            config.write(configfile)

    def remove_camera_pov(self, name):
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(self.path)
        config.remove_option('camera_pov_preset', name + '.eye')
        config.remove_option('camera_pov_preset', name + '.up')
        config.remove_option('camera_pov_preset', name + '.center')

        self.get_pov_presets_names()

        with open(self.path, 'w') as configfile:
            config.write(configfile)

    def get_camera_pov(self, name):
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(self.path)
        front = np.asarray(config.get('camera_pov_preset', name + '.front')[1:-1].split()).astype(np.float)
        lookat = np.asarray(config.get('camera_pov_preset', name + '.lookat')[1:-1].split()).astype(np.float)
        up = np.asarray(config.get('camera_pov_preset', name + '.up')[1:-1].split()).astype(np.float)
        zoom = float(config.get('camera_pov_preset', name + '.zoom'))
        current_camera_pov = {"front": front, 'lookat': lookat, 'up': up,'zoom':zoom}

        return current_camera_pov

    def get_pov_presets_names(self):
        self.pov_presets_names = list()

        read_config = configparser.ConfigParser()
        read_config.read(self.path)

        camera_pov_preset = read_config['camera_pov_preset']

        for keys in camera_pov_preset.keys():
            self.pov_presets_names.append(keys.split('.')[0])
        self.pov_presets_names = unique(self.pov_presets_names)
        self.pov_presets_names = np.sort(self.pov_presets_names)


