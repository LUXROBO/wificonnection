from notebook.utils import url_path_join as ujoin
from notebook.base.handlers import IPythonHandler
import os, json, urllib, requests
from subprocess import Popen, PIPE, TimeoutExpired, SubprocessError
import subprocess
import pandas as pd
from collections import OrderedDict

interface_name = 'wlx88366cf69460'
sudo_password = 'luxrobo'

class WifiHandler(IPythonHandler):
    
    # input system call parameter
    def select_cmd(self, x):

        # choose the commands want to call
        return {
            'iwconfig' : ['iwconfig'],
            'search_wifi_list' : ['sudo', 'iw', interface_name, 'scan'],
            'interface_down' : ['sudo', 'ifconfig', interface_name, 'down'],
            'interface_up' : ['sudo', 'ifconfig', interface_name, 'up'],
            'wpa_list' : ['wpa_cli', '-i', interface_name, 'list_networks'],
            'wpa_select_network' : ['wpa_cli', '-i', interface_name, 'select_network'],
            'is_wlan0_up' : ['sudo', 'iwlist', interface_name, 'scan'],
            'interface_reconfigure' : ['wpa_cli', '-i', interface_name, 'reconfigure'],
        }.get(x, None)

    def error_and_return(self, reason):

        # send error
        self.send_error(500, reason=reason)

    def interface_up(self):

        # raise the wireless interface 
        cmd = self.select_cmd('interface_up')
        try:
            subprocess.run(cmd)
        except SubprocessError as e:
            print(e)
            self.error_and_return('interface up error')
            return
        
        self.is_inter_up = True

    def interface_down(self):

        # kill the wireless interface
        cmd = self.select_cmd('interface_down')
        try:
            subprocess.run(cmd)
        except SubprocessError as e:
            print(e)
            self.error_and_return('interfae down error')
            return
        
        self.is_inter_up = False

    def is_interface_off(self, tmp_str):

        tmp_str = tmp_str.decode('utf-8')
        if tmp_str.find('Resource temporarily unavailable') != -1:
            return False
        elif tmp_str.find('Network is down') != -1:
            return True


    def get_current_wifi_info(self):
        
        wifi_info = [{
            'SSID' : None,
            'PSK' : None,
            'SIGNAL' : 0,
            'STATUS' : False
        }]

        cmd = self.select_cmd('iwconfig')
        try:
            with Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE) as proc:
                output = proc.communicate()
                output = [x.decode('utf-8') for x in output]
        except SubprocessError as e:
            print(e)
            self.error_and_return('Improper Popen object opened')
            return

        try:
            inter_info = [x for x in output if x.find(interface_name) != -1]
            assert len(inter_info) != 0
        except AssertionError as e:
            print(e)
            self.error_and_return("Cannot find wlan0 device interface")
            return

        inter_info = inter_info[0].split(' ')
        
        for data in inter_info:
            if data.find('ESSID') != -1:
                wlan0_info = data.split(':')[1]

        if wlan0_info != 'off/any':
            wifi_info[0]['SSID'] = wlan0_info
            wifi_info[0]['STATUS'] = True
            
        return wifi_info
    
    def is_wifi_connected(self, current_wifi_info):
        """ True/false whether wifi connected
        """

        return current_wifi_info.get('wifi_status')

    def scan_candidate_wifi(self):
        """ scanning candidate wifi information
            return : {
                'SSID' : ['PSK', 'Signal Strength']
            }
        """

        cmd = self.select_cmd('search_wifi_list')
        # scan wifi list
        self.is_inter_up = False
        while True:
            try:
                with Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE) as proc:
                    output = proc.communicate(input=(sudo_password+'\n').encode())
            except SubprocessError as e:
                print(e)
                self.error_and_return('Improper Popen object opened')
                return
            
            # wlan0 interface is already opened
            if output[1] == b'':
                self.is_inter_up = True
                break
            # wlan0 interface is closed or resource busy
            elif output[0] == b'':
                if self.is_interface_off(output[1]):
                    return
                else:
                    print('resource busy')
                    pass
            time.sleep(0.01)

        # parsing all ssid list
        ssid_cnt = 0
        tmp_scanned_wifi_info = dict()
        for each_line in output[0].decode('utf-8').split('\n'):
            tmp_each_info = []
            if each_line.find('BSS') != -1 and each_line.find(interface_name) != -1:
                if ssid_cnt != 0 and len(tmp_scanned_wifi_info.get(ssid_cnt)) == 2:
                    tmp_scanned_wifi_info[ssid_cnt].append("FREE")
                ssid_cnt += 1
                tmp_scanned_wifi_info[ssid_cnt] = []
            elif each_line.find('signal') != -1:
                tmp_scanned_wifi_info[ssid_cnt].append(int(float(each_line.split(' ')[1])))
            elif each_line.find('SSID:') != -1:
                tmp_ssid = each_line.split(' ')[1]
                if tmp_ssid != '' and tmp_ssid.find('x00') == -1:
                    tmp_scanned_wifi_info[ssid_cnt].append(tmp_ssid)
            elif each_line.find('RSN') != -1:
                tmp_scanned_wifi_info[ssid_cnt].append('PSK')

        # Sort out the duplicate value and generate json format 
        df_scanned_wifi_info = pd.DataFrame(data=tmp_scanned_wifi_info.values(),
                                                columns=['SIGNAL', 'SSID', 'PSK'])[['SSID', 'PSK', 'SIGNAL']]
        df_tmp_psk = df_scanned_wifi_info[['SSID', 'PSK']].drop_duplicates()
        df_tmp_signal = df_scanned_wifi_info.groupby('SSID').SIGNAL.min().reset_index(name = "SIGNAL")
        wifi_info = pd.merge(df_tmp_psk, df_tmp_signal, how="inner", on="SSID").sort_values(by=['SIGNAL']).to_dict('records')

        return wifi_info

    def is_pi_have_ssid(self, data):
        
        cmd = self.select_cmd('wpa_list')
        try:
            with Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE) as proc:
                output = proc.communicate(input=(sudo_password+'\n').encode())
        except SubprocessError as e:
            print(e)
            self.error_and_return('Improper Popen object opened')
            return

        target_ssid = data.get('ssid')
        output = output[0].decode('utf-8')
        target_line = [line for line in output.split('\n') if line.find(target_ssid) == -1]
        wifi_index = int(target_line[1][0])

        if wifi_index >= 0:
            return wifi_index
        else:
            return -1

    def select_network(self, index):
        cmd = self.select_cmd('wpa_select_network')
        cmd.append(str(index))

        try:
            subprocess.run(cmd)
        except SubprocessError as e:
            print(e)
            self.error_and_return('Improper Popen object opened')
            return

        # Check if wifi connect
        cmd = self.select_cmd('iwconfig')
        while True:
            wifi_info = self.get_current_wifi_info()
            if wifi_info.get('wifi_status'):
                break
            time.sleep(0.01)

        return wifi_info
                

class WifiGetter(WifiHandler):

    # return the possible wifi list
    def get(self):        
        """ Communication interface with jupyter notebook
        """

        # deteremine the wireless status of raspberry Pi
        wifi_list = self.scan_candidate_wifi()
        if self.is_inter_up:
            current_wifi_info = self.get_current_wifi_info()
            for each_info in wifi_list:
                if each_info.get('SSID') == 'DREAMPLUS_GUEST':
                    current_wifi_info[0]['PSK'] = each_info.get('PSK')
                    current_wifi_info[0]['STATUS'] = each_info.get('STATUS')

            self.write({'status' : 200, 
                        'statusText' : 'current wifi information',
                        'current_wifi_data' : current_wifi_info,
                        'whole_wifi_data' : wifi_list
            })
        else: 
            self.write({'status' : 200, 'statusText' : 'interface off'})

class WifiSetter(WifiHandler):
    
    def put(self):
        
        data = {
            'ssid' : 'DREAMPLUS_GEUST',
            'psk' : 'welcome#'
        }

        target_index = self.is_pi_have_ssid(data)
        # raspberrypi already have target wifi information
        if target_index >= 0:
            wifi_info = self.select_network(target_index)
        # raspberrypi do not have target wifi information
        else:
            pass


def setup_handlers(nbapp):
    # Determine whether wifi connected
    # route_pattern_current_wifi = ujoin(nbapp.settings['base_url'], '/wifi/current')
    # nbapp.add_handlers('.*', [(route_pattern_current_wifi, CurrentWifiHandler)])

    # Scanning wifi list
    route_pattern_wifi_list = ujoin(nbapp.settings['base_url'], '/wifi/scan')
    nbapp.add_handlers('.*', [(route_pattern_wifi_list, WifiGetter)])