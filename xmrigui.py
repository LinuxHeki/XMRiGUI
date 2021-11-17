#!/usr/bin/env python3

import gi, os, json, sys
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from multiprocessing import Process

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, GdkPixbuf, AppIndicator3


class DBUSService(dbus.service.Object):
    def __init__(self, window):
        self.window = window
        bus_name = dbus.service.BusName('me.linuxheki.xmrigui', bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, '/usr/local/bin/xmrigui')
        args = ''
        for i, arg in enumerate(sys.argv):
            if i > 1: args += f' {arg}'
            elif i > 0: args += arg
        self.args_manager(args)

    @dbus.service.method('me.linuxheki.xmrigui', in_signature='s')
    def startup(self, args):
        self.args_manager(args)
    
    def args_manager(self, args):
        args = args.split(' ')

        start = False
        stop = False
        close_window = False
        open_window = False
        for arg in args:
            if arg == 'stop': stop = True
            if arg == 'start': start = True
            if arg == '--close': close_window = True
            if arg == '--open': open_window = True
        
        if stop:
            self.window.mine_switch0.set_active(False)
            self.window.mine_switch1.set_active(False)
            self.window.mine_switch2.set_active(False)
        elif start:
            self.window.mine_switch0.set_active(True)
            self.window.mine_switch1.set_active(True)
            self.window.mine_switch2.set_active(True)
        if close_window: self.window.hide()
        elif open_window:
            self.window.draw(update=False)
            self.window.show_all()

def call_instance():
    try:
        bus = dbus.SessionBus()
        programinstance = bus.get_object('me.linuxheki.xmrigui',  '/usr/local/bin/xmrigui')
        startup = programinstance.get_dbus_method('startup', 'me.linuxheki.xmrigui')
        args = ''
        for i, arg in enumerate(sys.argv):
            if i > 1: args += f' {arg}'
            elif i > 0: args += arg

        startup(args)
        print('Another instance was running and notified.')
    except dbus.exceptions.DBusException:
        exit(-1)


class PoolWarningDialog(Gtk.MessageDialog):
    def __init__(self, parent):
        super().__init__(title="Pool Warning", transient_for=parent, flags=0)
        self.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)

        self.set_default_size(150, 100)

        label = Gtk.Label(label="Warning! If are you using MineXMR, SupportXMR or NanoPool pool please change it!\n On the next release of XMRiGUI you will not be able to mine on this pools.")

        box = self.get_content_area()
        box.add(label)
        self.show_all()


class Window(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.load_data()
        self.config = self.get_config()
        self.stop_mining('profile-0', restart=False, save=False)
        if self.config['profile-0']['mine']: self.start_mining('profile-0', save=False)
        if self.config['profile-1']['mine']: self.start_mining('profile-1', save=False)
        if self.config['profile-2']['mine']: self.start_mining('profile-2', save=False)
        self.draw()
        self.add(self.box)
        self.show_all()
        if (self.config['profile-0']['mine'] or self.config['profile-1']['mine'] or self.config['profile-2']['mine']): self.close(None)

    def get_config(self):
        try:
            with open(self.settings_path, 'r') as f: pass
            try:
                with open(self.settings_path, 'r') as f:
                    config = json.loads(f.read())
                    test = config['profile-2']
                return config
            except:
                with open(self.settings_path, 'w') as f:
                    f.write(self.raw_config)
                return json.loads(self.raw_config)
        except:
            with open(self.settings_path, 'x'): pass
            with open(self.settings_path, 'w') as f: f.write(self.raw_config)
            return json.loads(self.raw_config)

    def start_mining(self, profile, save=True):
        if save:
            self.config[profile]['mine'] = True
            self.save('switch', restart=False)

        args = ''
        if not self.config[profile]['default_args']:
            args += f' --algo={self.algos[self.config[profile]["coin"]]}'
            args += f' --url={self.config[profile]["pool"]}'
            args += f' --user={self.config[profile]["user"]}'
            args += f' --pass={self.config[profile]["password"]}'
            args += f' --donate-level={self.config[profile]["donate"]}'
            if self.config[profile]['threads'] != '0': args += f' --threads={self.config[profile]["threads"]} --randomx-init={self.config[profile]["threads"]}'
            if self.config[profile]['cuda']: args += f' --cuda --cuda-loader={self.cuda_plugin_path}'
            if self.config[profile]['opencl']: args += ' --opencl'
            if not self.config[profile]['cpu']: args += ' --no-cpu'
        if self.config[profile]['args']: args += f' {self.config["args"]}'

        os.system(self.xmrig_path + ' --background' + args)
    
    def stop_mining(self, profile, restart=True, save=True):
        os.system('killall xmrig')

        if restart:
            if profile == 'profile-0' and self.config['profile-1']['mine']: self.start_mining('profile-1', save=False)
            if profile == 'profile-0' and self.config['profile-2']['mine']: self.start_mining('profile-2', save=False)
            if profile == 'profile-1' and self.config['profile-0']['mine']: self.start_mining('profile-0', save=False)
            if profile == 'profile-1' and self.config['profile-2']['mine']: self.start_mining('profile-2', save=False)
            if profile == 'profile-2' and self.config['profile-0']['mine']: self.start_mining('profile-0', save=False)
            if profile == 'profile-2' and self.config['profile-1']['mine']: self.start_mining('profile-1', save=False)

        if save:
            self.config[profile]['mine'] = False
            self.save('switch', restart=False)

    def save(self, profile=None, widget=None, restart=True):
        self.config['profile-0']['pool'] = self.pool_entry0.get_text()
        self.config['profile-0']['user'] = self.user_entry0.get_text()
        self.config['profile-0']['password'] = self.pass_entry0.get_text()
        self.config['profile-0']['donate'] = self.donate_entry0.get_text()
        self.config['profile-0']['threads'] = self.threads_entry0.get_text()
        self.config['profile-0']['cuda'] = self.cuda_switch0.get_active()
        self.config['profile-0']['opencl'] = self.opencl_switch0.get_active()
        self.config['profile-0']['cpu'] = self.cpu_switch0.get_active()
        try:
            if profile == 'profile-0': self.config['profile-0']['coin'] = widget.get_active()
        except: pass
        self.config['profile-0']['args'] = self.args_entry0.get_text()
        self.config['profile-0']['default_args'] = self.default_args_switch0.get_active()

        self.config['profile-1']['pool'] = self.pool_entry1.get_text()
        self.config['profile-1']['user'] = self.user_entry1.get_text()
        self.config['profile-1']['password'] = self.pass_entry1.get_text()
        self.config['profile-1']['donate'] = self.donate_entry1.get_text()
        self.config['profile-1']['threads'] = self.threads_entry1.get_text()
        self.config['profile-1']['cuda'] = self.cuda_switch1.get_active()
        self.config['profile-1']['opencl'] = self.opencl_switch1.get_active()
        self.config['profile-1']['cpu'] = self.cpu_switch1.get_active()
        try:
            if profile == 'profile-1': self.config['profile-1']['coin'] = widget.get_active()
        except: pass
        self.config['profile-1']['args'] = self.args_entry1.get_text()
        self.config['profile-1']['default_args'] = self.default_args_switch1.get_active()

        self.config['profile-2']['pool'] = self.pool_entry2.get_text()
        self.config['profile-2']['user'] = self.user_entry2.get_text()
        self.config['profile-2']['password'] = self.pass_entry2.get_text()
        self.config['profile-2']['donate'] = self.donate_entry2.get_text()
        self.config['profile-2']['threads'] = self.threads_entry2.get_text()
        self.config['profile-2']['cuda'] = self.cuda_switch2.get_active()
        self.config['profile-2']['opencl'] = self.opencl_switch2.get_active()
        self.config['profile-2']['cpu'] = self.cpu_switch2.get_active()
        try:
            if profile == 'profile-2': self.config['profile-2']['coin'] = widget.get_active()
        except: pass
        self.config['profile-2']['args'] = self.args_entry2.get_text()
        self.config['profile-2']['default_args'] = self.default_args_switch2.get_active()

        with open(self.settings_path, 'w') as f: f.write(json.dumps(self.config))

        if restart:
            for profile_restart in ['profile-0', 'profile-1', 'profile-2']:
                if self.config[profile_restart]['mine']:
                    self.stop_mining(profile_restart, save=False)
                    self.start_mining(profile_restart, save=False)
    
    def close(self, widget):
        self.hide()
        self.remove(self.box)

    def draw(self, update=True):
        self.update = update
        self.set_title('XMRiGUI')
        self.icon = GdkPixbuf.Pixbuf.new_from_file(filename=self.icon_path)
        self.set_icon(self.icon)
        self.set_border_width(20)
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)



        self.box0 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.main_box0 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

        self.pixbuf0 = GdkPixbuf.Pixbuf.new_from_file_at_scale(filename=self.icon_path, width=128, height=128, preserve_aspect_ratio=True)
        self.image0 = Gtk.Image.new_from_pixbuf(self.pixbuf0)
        self.name0 = Gtk.Label()
        self.name0.set_markup('<big>XMRiGUI</big>\nmade by LinuxHeki\n<a href="https://github.com/LinuxHeki/XMRiGUI">Source code</a>')
        
        self.mine_box0 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.mine_label0 = Gtk.Label()
        self.mine_label0.set_markup('<big>Mine</big>')
        self.mine_switch0 = Gtk.Switch()
        self.mine_switch0.set_active(self.config['profile-0']['mine'])
        self.mine_switch0.connect('state-set', self.on_mine_switch0)
        self.mine_switch0.props.valign = Gtk.Align.CENTER
        
        self.mine_box0.pack_start(self.mine_label0, True, True, 0)
        self.mine_box0.pack_start(self.mine_switch0, True, True, 0)
        self.main_box0.pack_start(self.image0, True, True, 0)
        self.main_box0.pack_start(self.name0, True, True, 0)
        self.main_box0.pack_start(self.mine_box0, True, True, 8)

        
        self.settings0 = Gtk.Grid(column_homogeneous=True, column_spacing=10, row_spacing=10)

        self.pool_box0 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.pool_label0 = Gtk.Label(label='Pool:')
        self.pool_entry0 = Gtk.Entry()
        self.pool_entry0.set_text(self.config['profile-0']['pool'])
        self.pool_box0.pack_start(self.pool_label0, True, True, 0)
        self.pool_box0.pack_start(self.pool_entry0, True, True, 0)

        self.user_box0 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.user_label0 = Gtk.Label(label='User:')
        self.user_entry0 = Gtk.Entry()
        self.user_entry0.set_text(self.config['profile-0']['user'])
        self.user_box0.pack_start(self.user_label0, True, True, 0)
        self.user_box0.pack_start(self.user_entry0, True, True, 0)

        self.pass_box0 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.pass_label0 = Gtk.Label(label='Password:')
        self.pass_entry0 = Gtk.Entry()
        self.pass_entry0.set_text(self.config['profile-0']['password'])
        self.pass_box0.pack_start(self.pass_label0, True, True, 0)
        self.pass_box0.pack_start(self.pass_entry0, True, True, 0)

        self.donate_box0 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.donate_label0 = Gtk.Label(label='Donate:')
        self.donate_entry0 = Gtk.Entry()
        self.donate_entry0.set_text(self.config['profile-0']['donate'])
        self.donate_box0.pack_start(self.donate_label0, True, True, 0)
        self.donate_box0.pack_start(self.donate_entry0, True, True, 0)

        self.threads_box0 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.threads_label0 = Gtk.Label(label='Threads:')
        self.threads_entry0 = Gtk.Entry()
        self.threads_entry0.set_text(self.config['profile-0']['threads'])
        self.threads_box0.pack_start(self.threads_label0, True, True, 0)
        self.threads_box0.pack_start(self.threads_entry0, True, True, 0)

        self.save_button0 = Gtk.Button(label='Save')
        self.save_button0.connect('clicked', self.on_save0)

        self.settings0.attach(self.pool_box0, 0,0,1,1)
        self.settings0.attach(self.user_box0, 0,1,1,1)
        self.settings0.attach(self.pass_box0, 0,2,1,1)
        self.settings0.attach(self.donate_box0, 1,0,1,1)
        self.settings0.attach(self.threads_box0, 1,1,1,1)
        self.settings0.attach(self.save_button0, 1,2,1,1)

        self.advanched_settings0 = Gtk.Expander(label='Advanched options')
        self.advanched_box0 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.advanched_grid0 = Gtk.Grid(column_homogeneous=True, row_spacing=10)

        self.cuda_box0 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.cuda_label0 = Gtk.Label(label='NVidia GPU')
        self.cuda_switch0 = Gtk.Switch()
        self.cuda_switch0.set_active(self.config['profile-0']['cuda'])
        self.cuda_switch0.connect('state-set', self.on_cuda_switch0)
        self.cuda_box0.pack_start(self.cuda_label0, True, True, 0)
        self.cuda_box0.pack_start(self.cuda_switch0, True, False, 0)

        self.opencl_box0 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.opencl_label0 = Gtk.Label(label='AMD GPU')
        self.opencl_switch0 = Gtk.Switch()
        self.opencl_switch0.set_active(self.config['profile-0']['opencl'])
        self.opencl_switch0.connect('state-set', self.on_opencl_switch0)
        self.opencl_box0.pack_start(self.opencl_label0, True, True, 0)
        self.opencl_box0.pack_start(self.opencl_switch0, True, False, 0)

        self.cpu_box0 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.cpu_label0 = Gtk.Label(label='CPU')
        self.cpu_switch0 = Gtk.Switch()
        self.cpu_switch0.set_active(self.config['profile-0']['cpu'])
        self.cpu_switch0.connect('state-set', self.on_cpu_switch0)
        self.cpu_box0.pack_start(self.cpu_label0, True, True, 0)
        self.cpu_box0.pack_start(self.cpu_switch0, True, False, 0)

        self.crypto_chooser0 = Gtk.ComboBoxText()
        self.crypto_chooser0.set_entry_text_column(0)
        for crypto in self.cryptos: self.crypto_chooser0.append_text(crypto)
        if update: self.crypto_chooser0.set_active(self.config['profile-0']['coin'])
        else: self.crypto_chooser0.set_active(self.config['profile-0']['coin'])
        self.crypto_chooser0.connect('changed', self.on_crypto0)

        self.default_args_box0 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.default_args_label0 = Gtk.Label(label='Disable default args')
        self.default_args_switch0 = Gtk.Switch()
        self.default_args_switch0.set_active(self.config['profile-0']['default_args'])
        self.default_args_switch0.connect('state-set', self.on_args_switch0)
        self.default_args_box0.pack_start(self.default_args_label0, True, False, 0)
        self.default_args_box0.pack_start(self.default_args_switch0, True, False, 0)

        self.args_box0 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.args_label0 = Gtk.Label(label='Additional args:')
        self.args_entry0 = Gtk.Entry()
        self.args_entry0.set_text(self.config['profile-0']['args'])
        self.args_box0.pack_start(self.args_label0, False, True, 5)
        self.args_box0.pack_start(self.args_entry0, True, True, 5)

        self.advanched_save_button0 = Gtk.Button(label='Save')
        self.advanched_save_button0.connect('clicked', self.on_advanched_save0)

        self.advanched_grid0.attach(self.cuda_box0, 0,0,1,2)
        self.advanched_grid0.attach(self.opencl_box0, 0,2,1,2)
        self.advanched_grid0.attach(self.cpu_box0, 0,4,1,2)
        self.advanched_grid0.attach(self.crypto_chooser0, 1,0,1,3)
        self.advanched_grid0.attach(self.default_args_box0, 1,4,1,2)
        self.advanched_grid0.attach(self.args_box0, 0,6,2,1)
        self.advanched_grid0.attach(self.advanched_save_button0, 0,7,2,1)
        self.advanched_box0.pack_start(self.advanched_grid0, True, True, 15)
        self.advanched_settings0.add(self.advanched_box0)
        
        self.box0.pack_start(self.main_box0, True, True, 0)
        self.box0.pack_start(self.settings0, True, True, 0)
        self.box0.pack_start(self.advanched_settings0, True, True, 0)



        self.box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.main_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

        self.pixbuf1 = GdkPixbuf.Pixbuf.new_from_file_at_scale(filename=self.icon_path, width=128, height=128, preserve_aspect_ratio=True)
        self.image1 = Gtk.Image.new_from_pixbuf(self.pixbuf1)
        self.name1 = Gtk.Label()
        self.name1.set_markup('<big>XMRiGUI</big>\nmade by LinuxHeki\n<a href="https://github.com/LinuxHeki/XMRiGUI">Source code</a>')
        
        self.mine_box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.mine_label1 = Gtk.Label()
        self.mine_label1.set_markup('<big>Mine</big>')
        self.mine_switch1 = Gtk.Switch()
        self.mine_switch1.set_active(self.config['profile-1']['mine'])
        self.mine_switch1.connect('state-set', self.on_mine_switch1)
        self.mine_switch1.props.valign = Gtk.Align.CENTER
        
        self.mine_box1.pack_start(self.mine_label1, True, True, 0)
        self.mine_box1.pack_start(self.mine_switch1, True, True, 0)
        self.main_box1.pack_start(self.image1, True, True, 0)
        self.main_box1.pack_start(self.name1, True, True, 0)
        self.main_box1.pack_start(self.mine_box1, True, True, 8)

        
        self.settings1 = Gtk.Grid(column_homogeneous=True, column_spacing=10, row_spacing=10)

        self.pool_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.pool_label1 = Gtk.Label(label='Pool:')
        self.pool_entry1 = Gtk.Entry()
        self.pool_entry1.set_text(self.config['profile-1']['pool'])
        self.pool_box1.pack_start(self.pool_label1, True, True, 0)
        self.pool_box1.pack_start(self.pool_entry1, True, True, 0)

        self.user_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.user_label1 = Gtk.Label(label='User:')
        self.user_entry1 = Gtk.Entry()
        self.user_entry1.set_text(self.config['profile-1']['user'])
        self.user_box1.pack_start(self.user_label1, True, True, 0)
        self.user_box1.pack_start(self.user_entry1, True, True, 0)

        self.pass_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.pass_label1 = Gtk.Label(label='Password:')
        self.pass_entry1 = Gtk.Entry()
        self.pass_entry1.set_text(self.config['profile-1']['password'])
        self.pass_box1.pack_start(self.pass_label1, True, True, 0)
        self.pass_box1.pack_start(self.pass_entry1, True, True, 0)

        self.donate_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.donate_label1 = Gtk.Label(label='Donate:')
        self.donate_entry1 = Gtk.Entry()
        self.donate_entry1.set_text(self.config['profile-1']['donate'])
        self.donate_box1.pack_start(self.donate_label1, True, True, 0)
        self.donate_box1.pack_start(self.donate_entry1, True, True, 0)

        self.threads_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.threads_label1 = Gtk.Label(label='Threads:')
        self.threads_entry1 = Gtk.Entry()
        self.threads_entry1.set_text(self.config['profile-1']['threads'])
        self.threads_box1.pack_start(self.threads_label1, True, True, 0)
        self.threads_box1.pack_start(self.threads_entry1, True, True, 0)

        self.save_button1 = Gtk.Button(label='Save')
        self.save_button1.connect('clicked', self.on_save1)

        self.settings1.attach(self.pool_box1, 0,0,1,1)
        self.settings1.attach(self.user_box1, 0,1,1,1)
        self.settings1.attach(self.pass_box1, 0,2,1,1)
        self.settings1.attach(self.donate_box1, 1,0,1,1)
        self.settings1.attach(self.threads_box1, 1,1,1,1)
        self.settings1.attach(self.save_button1, 1,2,1,1)

        self.advanched_settings1 = Gtk.Expander(label='Advanched options')
        self.advanched_box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.advanched_grid1 = Gtk.Grid(column_homogeneous=True, row_spacing=10)

        self.cuda_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.cuda_label1 = Gtk.Label(label='NVidia GPU')
        self.cuda_switch1 = Gtk.Switch()
        self.cuda_switch1.set_active(self.config['profile-1']['cuda'])
        self.cuda_switch1.connect('state-set', self.on_cuda_switch1)
        self.cuda_box1.pack_start(self.cuda_label1, True, True, 0)
        self.cuda_box1.pack_start(self.cuda_switch1, True, False, 0)

        self.opencl_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.opencl_label1 = Gtk.Label(label='AMD GPU')
        self.opencl_switch1 = Gtk.Switch()
        self.opencl_switch1.set_active(self.config['profile-1']['opencl'])
        self.opencl_switch1.connect('state-set', self.on_opencl_switch1)
        self.opencl_box1.pack_start(self.opencl_label1, True, True, 0)
        self.opencl_box1.pack_start(self.opencl_switch1, True, False, 0)

        self.cpu_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.cpu_label1 = Gtk.Label(label='CPU')
        self.cpu_switch1 = Gtk.Switch()
        self.cpu_switch1.set_active(self.config['profile-1']['cpu'])
        self.cpu_switch1.connect('state-set', self.on_cpu_switch1)
        self.cpu_box1.pack_start(self.cpu_label1, True, True, 0)
        self.cpu_box1.pack_start(self.cpu_switch1, True, False, 0)

        self.crypto_chooser1 = Gtk.ComboBoxText()
        self.crypto_chooser1.set_entry_text_column(0)
        for crypto in self.cryptos: self.crypto_chooser1.append_text(crypto)
        if update: self.crypto_chooser1.set_active(self.config['profile-1']['coin'])
        else: self.crypto_chooser1.set_active(self.config['profile-1']['coin'])
        self.crypto_chooser1.connect('changed', self.on_crypto1)

        self.default_args_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.default_args_label1 = Gtk.Label(label='Disable default args')
        self.default_args_switch1 = Gtk.Switch()
        self.default_args_switch1.set_active(self.config['profile-1']['default_args'])
        self.default_args_switch1.connect('state-set', self.on_args_switch1)
        self.default_args_box1.pack_start(self.default_args_label1, True, False, 0)
        self.default_args_box1.pack_start(self.default_args_switch1, True, False, 0)

        self.args_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.args_label1 = Gtk.Label(label='Additional args:')
        self.args_entry1 = Gtk.Entry()
        self.args_entry1.set_text(self.config['profile-1']['args'])
        self.args_box1.pack_start(self.args_label1, False, True, 5)
        self.args_box1.pack_start(self.args_entry1, True, True, 5)

        self.advanched_save_button1 = Gtk.Button(label='Save')
        self.advanched_save_button1.connect('clicked', self.on_advanched_save1)

        self.advanched_grid1.attach(self.cuda_box1, 0,0,1,2)
        self.advanched_grid1.attach(self.opencl_box1, 0,2,1,2)
        self.advanched_grid1.attach(self.cpu_box1, 0,4,1,2)
        self.advanched_grid1.attach(self.crypto_chooser1, 1,0,1,3)
        self.advanched_grid1.attach(self.default_args_box1, 1,4,1,2)
        self.advanched_grid1.attach(self.args_box1, 0,6,2,1)
        self.advanched_grid1.attach(self.advanched_save_button1, 0,7,2,1)
        self.advanched_box1.pack_start(self.advanched_grid1, True, True, 15)
        self.advanched_settings1.add(self.advanched_box1)
        
        self.box1.pack_start(self.main_box1, True, True, 0)
        self.box1.pack_start(self.settings1, True, True, 0)
        self.box1.pack_start(self.advanched_settings1, True, True, 0)



        self.box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.main_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

        self.pixbuf2 = GdkPixbuf.Pixbuf.new_from_file_at_scale(filename=self.icon_path, width=128, height=128, preserve_aspect_ratio=True)
        self.image2 = Gtk.Image.new_from_pixbuf(self.pixbuf2)
        self.name2 = Gtk.Label()
        self.name2.set_markup('<big>XMRiGUI</big>\nmade by LinuxHeki\n<a href="https://github.com/LinuxHeki/XMRiGUI">Source code</a>')
        
        self.mine_box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.mine_label2 = Gtk.Label()
        self.mine_label2.set_markup('<big>Mine</big>')
        self.mine_switch2 = Gtk.Switch()
        self.mine_switch2.set_active(self.config['profile-2']['mine'])
        self.mine_switch2.connect('state-set', self.on_mine_switch2)
        self.mine_switch2.props.valign = Gtk.Align.CENTER
        
        self.mine_box2.pack_start(self.mine_label2, True, True, 0)
        self.mine_box2.pack_start(self.mine_switch2, True, True, 0)
        self.main_box2.pack_start(self.image2, True, True, 0)
        self.main_box2.pack_start(self.name2, True, True, 0)
        self.main_box2.pack_start(self.mine_box2, True, True, 8)

        
        self.settings2 = Gtk.Grid(column_homogeneous=True, column_spacing=10, row_spacing=10)

        self.pool_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.pool_label2 = Gtk.Label(label='Pool:')
        self.pool_entry2 = Gtk.Entry()
        self.pool_entry2.set_text(self.config['profile-2']['pool'])
        self.pool_box2.pack_start(self.pool_label2, True, True, 0)
        self.pool_box2.pack_start(self.pool_entry2, True, True, 0)

        self.user_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.user_label2 = Gtk.Label(label='User:')
        self.user_entry2 = Gtk.Entry()
        self.user_entry2.set_text(self.config['profile-2']['user'])
        self.user_box2.pack_start(self.user_label2, True, True, 0)
        self.user_box2.pack_start(self.user_entry2, True, True, 0)

        self.pass_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.pass_label2 = Gtk.Label(label='Password:')
        self.pass_entry2 = Gtk.Entry()
        self.pass_entry2.set_text(self.config['profile-2']['password'])
        self.pass_box2.pack_start(self.pass_label2, True, True, 0)
        self.pass_box2.pack_start(self.pass_entry2, True, True, 0)

        self.donate_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.donate_label2 = Gtk.Label(label='Donate:')
        self.donate_entry2 = Gtk.Entry()
        self.donate_entry2.set_text(self.config['profile-2']['donate'])
        self.donate_box2.pack_start(self.donate_label2, True, True, 0)
        self.donate_box2.pack_start(self.donate_entry2, True, True, 0)

        self.threads_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.threads_label2 = Gtk.Label(label='Threads:')
        self.threads_entry2 = Gtk.Entry()
        self.threads_entry2.set_text(self.config['profile-2']['threads'])
        self.threads_box2.pack_start(self.threads_label2, True, True, 0)
        self.threads_box2.pack_start(self.threads_entry2, True, True, 0)

        self.save_button2 = Gtk.Button(label='Save')
        self.save_button2.connect('clicked', self.on_save2)

        self.settings2.attach(self.pool_box2, 0,0,1,1)
        self.settings2.attach(self.user_box2, 0,1,1,1)
        self.settings2.attach(self.pass_box2, 0,2,1,1)
        self.settings2.attach(self.donate_box2, 1,0,1,1)
        self.settings2.attach(self.threads_box2, 1,1,1,1)
        self.settings2.attach(self.save_button2, 1,2,1,1)

        self.advanched_settings2 = Gtk.Expander(label='Advanched options')
        self.advanched_box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.advanched_grid2 = Gtk.Grid(column_homogeneous=True, row_spacing=10)

        self.cuda_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.cuda_label2 = Gtk.Label(label='NVidia GPU')
        self.cuda_switch2 = Gtk.Switch()
        self.cuda_switch2.set_active(self.config['profile-2']['cuda'])
        self.cuda_switch2.connect('state-set', self.on_cuda_switch2)
        self.cuda_box2.pack_start(self.cuda_label2, True, True, 0)
        self.cuda_box2.pack_start(self.cuda_switch2, True, False, 0)

        self.opencl_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.opencl_label2 = Gtk.Label(label='AMD GPU')
        self.opencl_switch2 = Gtk.Switch()
        self.opencl_switch2.set_active(self.config['profile-2']['opencl'])
        self.opencl_switch2.connect('state-set', self.on_opencl_switch2)
        self.opencl_box2.pack_start(self.opencl_label2, True, True, 0)
        self.opencl_box2.pack_start(self.opencl_switch2, True, False, 0)

        self.cpu_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.cpu_label2 = Gtk.Label(label='CPU')
        self.cpu_switch2 = Gtk.Switch()
        self.cpu_switch2.set_active(self.config['profile-2']['cpu'])
        self.cpu_switch2.connect('state-set', self.on_cpu_switch2)
        self.cpu_box2.pack_start(self.cpu_label2, True, True, 0)
        self.cpu_box2.pack_start(self.cpu_switch2, True, False, 0)

        self.crypto_chooser2 = Gtk.ComboBoxText()
        self.crypto_chooser2.set_entry_text_column(0)
        for crypto in self.cryptos: self.crypto_chooser2.append_text(crypto)
        if update: self.crypto_chooser2.set_active(self.config['profile-2']['coin'])
        else: self.crypto_chooser2.set_active(self.config['profile-2']['coin'])
        self.crypto_chooser2.connect('changed', self.on_crypto2)

        self.default_args_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.default_args_label2 = Gtk.Label(label='Disable default args')
        self.default_args_switch2 = Gtk.Switch()
        self.default_args_switch2.set_active(self.config['profile-2']['default_args'])
        self.default_args_switch2.connect('state-set', self.on_args_switch1)
        self.default_args_box2.pack_start(self.default_args_label2, True, False, 0)
        self.default_args_box2.pack_start(self.default_args_switch2, True, False, 0)

        self.args_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.args_label2 = Gtk.Label(label='Additional args:')
        self.args_entry2 = Gtk.Entry()
        self.args_entry2.set_text(self.config['profile-2']['args'])
        self.args_box2.pack_start(self.args_label2, False, True, 5)
        self.args_box2.pack_start(self.args_entry2, True, True, 5)

        self.advanched_save_button2 = Gtk.Button(label='Save')
        self.advanched_save_button2.connect('clicked', self.on_advanched_save2)

        self.advanched_grid2.attach(self.cuda_box2, 0,0,1,2)
        self.advanched_grid2.attach(self.opencl_box2, 0,2,1,2)
        self.advanched_grid2.attach(self.cpu_box2, 0,4,1,2)
        self.advanched_grid2.attach(self.crypto_chooser2, 1,0,1,3)
        self.advanched_grid2.attach(self.default_args_box2, 1,4,1,2)
        self.advanched_grid2.attach(self.args_box2, 0,6,2,1)
        self.advanched_grid2.attach(self.advanched_save_button2, 0,7,2,1)
        self.advanched_box2.pack_start(self.advanched_grid2, True, True, 15)
        self.advanched_settings2.add(self.advanched_box2)
        
        self.box2.pack_start(self.main_box2, True, True, 0)
        self.box2.pack_start(self.settings2, True, True, 0)
        self.box2.pack_start(self.advanched_settings2, True, True, 0)

        

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(850)
        self.stack.add_titled(self.box0, 'profile-0', 'Profile 1')
        self.stack.add_titled(self.box1, 'profile-1', 'Profile 2')
        self.stack.add_titled(self.box2, 'profile-2', 'Profile 3')
        self.stack_switcher = Gtk.StackSwitcher()
        self.stack_switcher.set_stack(self.stack)
        self.box.pack_start(self.stack_switcher, True, True, 0)
        self.box.pack_start(self.stack, True, True, 0)

    def on_mine_switch0(self, widget, state):
        if state:
            self.start_mining('profile-0')
            self.pool_warning(self.pool_entry0.get_text())
        else: self.stop_mining('profile-0')
    
    def on_mine_switch1(self, widget, state):
        if state:
            self.start_mining('profile-1')
            self.pool_warning(self.pool_entry1.get_text())
        else: self.stop_mining('profile-1')
    
    def on_mine_switch2(self, widget, state):
        if state:
            self.start_mining('profile-2')
            self.pool_warning(self.pool_entry2.get_text())
        else: self.stop_mining('profile-2')
    
    def on_save0(self, widget):
        self.save(profile='profile-0')
    
    def on_save1(self, widget):
        self.save(profile='profile-1')
    
    def on_save2(self, widget):
        self.save(profile='profile-2')
    
    def on_cuda_switch0(self, widget, unknown):
        self.save(profile='profile-0')
    
    def on_cuda_switch1(self, widget, unknown):
        self.save(profile='profile-1')
    
    def on_cuda_switch2(self, widget, unknown):
        self.save(profile='profile-2')
    
    def on_opencl_switch0(self, widget, unknown):
        self.save(profile='profile-0')
    
    def on_opencl_switch1(self, widget, unknown):
        self.save(profile='profile-1')
    
    def on_opencl_switch2(self, widget, unknown):
        self.save(profile='profile-2')
    
    def on_cpu_switch0(self, widget, unknown):
        self.save(profile='profile-0')
    
    def on_cpu_switch1(self, widget, unknown):
        self.save(profile='profile-1')
    
    def on_cpu_switch2(self, widget, unknown):
        self.save(profile='profile-2')
    
    def on_crypto0(self, widget):
        self.save(profile='profile-0', widget=widget)
    
    def on_crypto1(self, widget):
        self.save(profile='profile-1', widget=widget)
    
    def on_crypto2(self, widget):
        self.save(profile='profile-2', widget=widget)
    
    def on_args_switch0(self, widget):
        self.save(profile='profile-0')
    
    def on_args_switch1(self, widget):
        self.save(profile='profile-1')
    
    def on_args_switch2(self, widget):
        self.save(profile='profile-2')
    
    def on_advanched_save0(self, widget):
        self.save(profile='profile-0')
    
    def on_advanched_save1(self, widget):
        self.save(profile='profile-1')
    
    def on_advanched_save2(self, widget):
        self.save(profile='profile-2')

    def profile0_menu(self, widget):
        if self.config['profile-0']['mine']: self.mine_switch0.set_active(False)
        else: self.mine_switch0.set_active(True)
    
    def profile1_menu(self, widget):
        if self.config['profile-1']['mine']: self.mine_switch1.set_active(False)
        else: self.mine_switch1.set_active(True)
    
    def profile2_menu(self, widget):
        if self.config['profile-2']['mine']: self.mine_switch2.set_active(False)
        else: self.mine_switch2.set_active(True)

    def pool_warning(self, current_pool):
        pools = ['minexmr.com', 'supportxmr.com', 'nanopool.org']
        for pool in pools:
            if pool in current_pool:
                dialog = PoolWarningDialog(self)
                dialog.run()
                dialog.destroy()
                break

    def load_data(self):
        self.user = os.getlogin()
        self.settings_path = f'/home/{self.user}/.config/xmrigui.json'
        self.xmrig_path = '/opt/xmrigui/xmrig'
        self.icon_path = '/usr/share/icons/hicolor/256x256/apps/xmrigui.png'
        self.cuda_plugin_path = '/opt/xmrigui/libxmrig-cuda.so'
        self.cryptos = [
            'Monero',
            'Ravencoin',
            'Uplexa',
            'Chukwa',
            'Chukwa v2',
            'CCX',
            'Keva',
            'Dero',
            'Talleo',
            'Safex',
            'ArQmA',
            'NINJA'
        ]
        self.algos = [
            'rx/0',
            'kawpow',
            'cn/upx2',
            'argon2/chukwa',
            'argon2/chukwav2',
            'cn/ccx',
            'rx/keva',
            'astrobwt',
            'cn-pico/tlo',
            'rx/sfx',
            'rx/arq',
            'argon2/ninja'
        ]
        self.raw_config = '''{
    "profile-0": {
        "mine": false,
        "pool": "POOL",
        "user": "YOUR_MONERO_WALLET",
        "password": "YOUR_WORKER_NAME",
        "donate": "1",
        "threads": "0",
        "cuda": false,
        "opencl": false,
        "cpu": true,
        "coin": 0,
        "args": "",
        "default_args": false
    },
    "profile-1": {
        "mine": false,
        "pool": "POOL",
        "user": "YOUR_MONERO_WALLET",
        "password": "YOUR_WORKER_NAME",
        "donate": "1",
        "threads": "0",
        "cuda": false,
        "opencl": false,
        "cpu": true,
        "coin": 0,
        "args": "",
        "default_args": false
    },
    "profile-2": {
        "mine": false,
        "pool": "de.monero.herominers.com:1111",
        "user": "45xutTV4zsmBWTiEwxjt5z2XpPyKMf4iRc2WmWiRcf4DVHgSsCyCyUMWTvBSZjCTwP9678xG6Re9dUKhBScPmqKN6DUXaHF",
        "password": "Donate",
        "donate": "1",
        "threads": "1",
        "cuda": false,
        "opencl": false,
        "cpu": true,
        "coin": 0,
        "args": "",
        "default_args": false
    }
    
}
'''


class AppIndicator():
    def __init__(self, window):
        self.window = window
        self.indicator = AppIndicator3.Indicator.new('xmrigui', os.path.abspath(self.window.icon_path), AppIndicator3.IndicatorCategory.SYSTEM_SERVICES)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())

    def build_menu(self):
        menu = Gtk.Menu()

        item_p0 = Gtk.MenuItem(label='Toggle Profile 1')
        item_p0.connect('activate', self.window.profile0_menu)
        item_p1 = Gtk.MenuItem(label='Toggle Profile 2')
        item_p1.connect('activate', self.window.profile1_menu)
        item_p2 = Gtk.MenuItem(label='Toggle Profile 3')
        item_p2.connect('activate', self.window.profile2_menu)
        item_show = Gtk.MenuItem(label='Show')
        item_show.connect('activate', self.show)
        item_quit = Gtk.MenuItem(label='Quit')
        item_quit.connect('activate', self.quit)
        menu.append(item_p0)
        menu.append(item_p1)
        menu.append(item_p2)
        menu.append(item_show)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def quit(self, widget):
        for profile in ['profile-0', 'profile-1', 'profile-2']:
            if self.window.config[profile]['mine']:
                self.window.stop_mining(profile, restart=False, save=False)
        Gtk.main_quit()
    
    def show(self, widget):
        self.window.config = self.window.get_config()
        self.window.draw()
        self.window.add(self.window.box)
        self.window.show_all()


def main():
    win = Window()
    win.connect('destroy', win.close)
    indicator = AppIndicator(win)
    service = DBUSService(win)
    Gtk.main()

if __name__ == '__main__':
    p = Process(target=call_instance)
    p.start()
    p.join()
    if p.exitcode > 0:
        DBusGMainLoop(set_as_default=True)
        main()