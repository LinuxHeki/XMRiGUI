#!/usr/bin/env python3

import gi
import os
import json
import sys
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

    @dbus.service.method('me.linuxheki.xmrigui', in_signature='s')
    def startup(self, args):
        self.args_manager(args)
    
    def args_manager(self, args):
        args = args.split(' ')

        close_window = False
        open_window = False
        start = False
        stop = False
        for arg in args:
            if arg == '--close': close_window = True
            if arg == '--open': open_window = True
            if arg == 'stop': stop = True
            if arg == 'start': start = True
        
        if stop:
            self.window.mine_switch.set_active(False)
        elif start:
            self.window.mine_switch.set_active(True)
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


class XMRiGUI(Gtk.Window):
    def __init__(self):
        super().__init__()
        self.load_data()
        self.config = self.get_config()
        self.draw()
        self.stop_mining(save=False)
        if self.config['mine']: self.start_mining(save=False)

    def get_config(self):
        try:
            with open(self.settings_path, 'r') as f: pass
            try:
                with open(self.settings_path, 'r') as f:
                    config = json.loads(f.read())
                    test = config['coin']
                return config
            except:
                with open(self.settings_path, 'w') as f:
                    f.write(self.raw_config)
                return json.loads(self.raw_config)
        except:
            with open(self.settings_path, 'x'): pass
            with open(self.settings_path, 'w') as f: f.write(self.raw_config)
            return json.loads(self.raw_config)

    def start_mining(self, save=True):
        if save:
            self.config['mine'] = True
            self.save('switch', restart=False)
        
        args = ''
        args += f' --algo={self.algos[self.config["coin"]]}'
        args += f' --url={self.config["pool"]}'
        args += f' --user={self.config["user"]}'
        args += f' --pass={self.config["password"]}'
        args += f' --donate-level={self.config["donate"]}'
        if self.config['threads'] != '0': args += f' --threads={self.config["threads"]}'
        if self.config['cuda']: args += f' --cuda --cuda-loader={self.cuda_plugin_path}'
        if self.config['opencl']: args += ' --opencl'
        if not self.config['cpu']: args += ' --no-cpu'

        os.system(self.xmrig_path + ' --background' + args)
    
    def stop_mining(self, save=True):
        if save:
            self.config['mine'] = False
            self.save('switch', restart=False)
        os.system('killall xmrig')

    def save(self, widget=None, restart=True):
        self.config['pool'] = self.pool_entry.get_text()
        self.config['user'] = self.user_entry.get_text()
        self.config['password'] = self.pass_entry.get_text()
        self.config['donate'] = self.donate_entry.get_text()
        self.config['threads'] = self.threads_entry.get_text()
        self.config['cuda'] = self.cuda_switch.get_active()
        self.config['opencl'] = self.opencl_switch.get_active()
        self.config['cpu'] = self.cpu_switch.get_active()
        try:
            self.config['coin'] = widget.get_active()
        except: pass

        with open(self.settings_path, 'w') as f: f.write(json.dumps(self.config))

        if restart and self.config['mine']:
            self.stop_mining(save=False)
            self.start_mining(save=False)
    
    def close(self, widget):
        self.hide()

    def draw(self, update=True):
        self.update = update
        self.set_title('XMRiGUI')
        self.icon = GdkPixbuf.Pixbuf.new_from_file(filename=self.icon_path)
        self.set_icon(self.icon)
        self.set_border_width(20)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.add(self.box)
        

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

        self.pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(filename=self.icon_path, width=128, height=128, preserve_aspect_ratio=True)
        self.image = Gtk.Image.new_from_pixbuf(self.pixbuf)
        self.name = Gtk.Label()
        self.name.set_markup('<big>XMRiGUI</big>\nmade by LinuxHeki\n<a href="https://github.com/LinuxHeki/XMRiGUI">Source code</a>')
        
        self.mine_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.mine_label = Gtk.Label()
        self.mine_label.set_markup('<big>Mine</big>')
        self.mine_switch = Gtk.Switch()
        self.mine_switch.set_active(self.config['mine'])
        self.mine_switch.connect('state-set', self.on_mine_switch)
        self.mine_switch.props.valign = Gtk.Align.CENTER
        
        self.mine_box.pack_start(self.mine_label, True, True, 0)
        self.mine_box.pack_start(self.mine_switch, True, True, 0)
        self.main_box.pack_start(self.image, True, True, 0)
        self.main_box.pack_start(self.name, True, True, 0)
        self.main_box.pack_start(self.mine_box, True, True, 8)

        
        self.settings = Gtk.Grid(column_homogeneous=True, column_spacing=10, row_spacing=10)

        self.pool_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.pool_label = Gtk.Label(label='Pool:')
        self.pool_entry = Gtk.Entry()
        self.pool_entry.set_text(self.config['pool'])
        self.pool_box.pack_start(self.pool_label, True, True, 0)
        self.pool_box.pack_start(self.pool_entry, True, True, 0)

        self.user_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.user_label = Gtk.Label(label='User:')
        self.user_entry = Gtk.Entry()
        self.user_entry.set_text(self.config['user'])
        self.user_box.pack_start(self.user_label, True, True, 0)
        self.user_box.pack_start(self.user_entry, True, True, 0)

        self.pass_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.pass_label = Gtk.Label(label='Password:')
        self.pass_entry = Gtk.Entry()
        self.pass_entry.set_text(self.config['password'])
        self.pass_box.pack_start(self.pass_label, True, True, 0)
        self.pass_box.pack_start(self.pass_entry, True, True, 0)

        self.donate_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.donate_label = Gtk.Label(label='Donate:')
        self.donate_entry = Gtk.Entry()
        self.donate_entry.set_text(self.config['donate'])
        self.donate_box.pack_start(self.donate_label, True, True, 0)
        self.donate_box.pack_start(self.donate_entry, True, True, 0)

        self.threads_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.threads_label = Gtk.Label(label='Threads:')
        self.threads_entry = Gtk.Entry()
        self.threads_entry.set_text(self.config['threads'])
        self.threads_box.pack_start(self.threads_label, True, True, 0)
        self.threads_box.pack_start(self.threads_entry, True, True, 0)

        self.save_button = Gtk.Button(label='Save')
        self.save_button.connect('clicked', self.on_save)

        self.settings.attach(self.pool_box, 0,0,1,1)
        self.settings.attach(self.user_box, 0,1,1,1)
        self.settings.attach(self.pass_box, 0,2,1,1)
        self.settings.attach(self.donate_box, 1,0,1,1)
        self.settings.attach(self.threads_box, 1,1,1,1)
        self.settings.attach(self.save_button, 1,2,1,1)

        self.advanched_settings = Gtk.Expander(label='Advanched options')
        self.advanched_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.advanched_grid = Gtk.Grid(column_homogeneous=True, row_spacing=10)

        self.cuda_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.cuda_label = Gtk.Label(label='NVidia GPU')
        self.cuda_switch = Gtk.Switch()
        self.cuda_switch.connect('state-set', self.on_cuda_switch)
        self.cuda_switch.set_active(self.config['cuda'])
        self.cuda_box.pack_start(self.cuda_label, True, False, 0)
        self.cuda_box.pack_start(self.cuda_switch, True, False, 0)

        self.opencl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.opencl_label = Gtk.Label(label='AMD GPU')
        self.opencl_switch = Gtk.Switch()
        self.opencl_switch.connect('state-set', self.on_opencl_switch)
        self.opencl_switch.set_active(self.config['opencl'])
        self.opencl_box.pack_start(self.opencl_label, True, False, 0)
        self.opencl_box.pack_start(self.opencl_switch, True, False, 0)

        self.cpu_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.cpu_label = Gtk.Label(label='CPU')
        self.cpu_switch = Gtk.Switch()
        self.cpu_switch.connect('state-set', self.on_cpu_switch)
        self.cpu_switch.set_active(self.config['cpu'])
        self.cpu_box.pack_start(self.cpu_label, True, False, 0)
        self.cpu_box.pack_start(self.cpu_switch, True, False, 0)

        self.crypto_chooser = Gtk.ComboBoxText()
        self.crypto_chooser.set_entry_text_column(0)
        for crypto in self.cryptos: self.crypto_chooser.append_text(crypto)
        if update: self.crypto_chooser.set_active(self.config['coin'])
        else: self.crypto_chooser.set_active(self.config['coin'])
        self.crypto_chooser.connect('changed', self.on_crypto)

        self.advanched_save_button = Gtk.Button(label='Save')
        self.advanched_save_button.connect('clicked', self.on_advanched_save)

        self.advanched_grid.attach(self.cuda_box, 0,0,1,2)
        self.advanched_grid.attach(self.opencl_box, 0,2,1,2)
        self.advanched_grid.attach(self.cpu_box, 0,4,1,2)
        self.advanched_grid.attach(self.crypto_chooser, 1,0,1,3)
        self.advanched_grid.attach(self.advanched_save_button, 1,3,1,3)
        self.advanched_box.pack_start(self.advanched_grid, True, True, 20)
        self.advanched_settings.add(self.advanched_box)
        
        self.box.pack_start(self.main_box, True, True, 0)
        self.box.pack_start(self.settings, True, True, 0)
        self.box.pack_start(self.advanched_settings, True, True, 0)

    def on_mine_switch(self, widget, state):
        if state: self.start_mining()
        else: self.stop_mining()
    
    def on_save(self, widget):
        self.save()
    
    def on_cuda_switch(self, widget):
        self.save()
    
    def on_opencl_switch(self, widget):
        self.save()
    
    def on_cpu_switch(self, widget, unknown):
        self.save()
    
    def on_crypto(self, widget):
        self.save(widget=widget)
    
    def on_advanched_save(self, widget):
        self.save()

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
    "mine": false,
    "pool": "POOL",
    "user": "YOUR_MONERO_WALLET",
    "password": "PASSWORD / YOUR_WORKER_NAME",
    "donate": "1",
    "threads": "0",
    "cuda": false,
    "opencl": false,
    "cpu": true,
    "coin": 0
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

        item_show = Gtk.MenuItem(label='Show')
        item_show.connect('activate', self.show)
        menu.append(item_show)
        item_quit = Gtk.MenuItem(label='Quit')
        item_quit.connect('activate', self.quit)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def quit(self, widget):
        if self.window.config['mine']:
            self.window.stop_mining(save=False)
        Gtk.main_quit()
    
    def show(self, widget):
        self.window.config = self.window.get_config()
        self.window.draw()
        self.window.show_all()


def main():
    win = XMRiGUI()
    win.connect('destroy', win.close)
    if not win.config['mine']: win.show_all()
    indicator = AppIndicator(win)
    myservice = DBUSService(win)
    Gtk.main()

if __name__ == '__main__':
    p = Process(target=call_instance)
    p.start()
    p.join()
    if p.exitcode > 0:
        DBusGMainLoop(set_as_default=True)
        main()