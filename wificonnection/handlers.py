from notebook.utils import url_path_join as ujoin
from notebook.base.handlers import IPythonHandler
import os, json, urllib, requests
from subprocess import Popen, PIPE, TimeoutExpired, SubprocessError
import subprocess
import pandas as pd
from collections import OrderedDict
import time

whole_wifi_info = []
current_wifi_info = []
temp_conf = str()

class WifiHandler(IPythonHandler):

    interface_name = 'wlan0'
    sudo_password = 'raspberrypi'
    wpa_supplicant = '/etc/wpa_supplicant/wpa_supplicant.conf'
    user_directory = './temp.conf'
    temp_user_directory = './copied_temp.conf'
    known_host_directory = '~/known_host.txt'
    
    # input system call parameter
    def select_cmd(self, x):
        # choose the commands want to call
        return {
            'iwconfig' : ['iwconfig'],
            'search_wifi_list' : ['sudo', 'iw', WifiHandler.interface_name, 'scan'],
            'interface_down' : ['sudo', 'ifconfig', WifiHandler.interface_name, 'down'],
            'interface_up' : ['sudo', 'ifconfig', WifiHandler.interface_name, 'up'],
            'wpa_list' : ['wpa_cli', '-i', WifiHandler.interface_name, 'list_networks'],
            'wpa_select_network' : ['wpa_cli', '-i', WifiHandler.interface_name, 'select_network'],
            'is_wlan0_up' : ['sudo', 'iwlist', WifiHandler.interface_name, 'scan'],
            'interface_reconfigure' : ['wpa_cli', '-i', WifiHandler.interface_name, 'reconfigure'],
            'copy_wpa_supplicant' : ['sudo', 'cp', '-f', WifiHandler.wpa_supplicant, WifiHandler.user_directory],
            'remove_temp_wpa_supplicant' : ['sudo', 'rm', '-rf', './*.conf'],
            'replace_mv_wpa_supplicant' : ['sudo', 'mv', WifiHandler.user_directory, WifiHandler.wpa_supplicant],
            'replace_mv_temp_wpa_supplicant' : ['sudo', 'mv', WifiHandler.temp_user_directory, WifiHandler.wpa_supplicant],
            'copy_temp_wpa_supplicant' : ['sudo', 'cp', WifiHandler.user_directory, WifiHandler.temp_user_directory],
            'change_mode' : ['sudo', 'chmod', '777', WifiHandler.user_directory]
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
            with Popen(['iwconfig'], stdin=PIPE, stdout=PIPE, stderr=PIPE) as proc:
                output = proc.communicate()
                output = [x.decode('utf-8') for x in output]
        except SubprocessError as e:
            print(e)
            self.error_and_return('Improper Popen object opened')
            return
        try:
            inter_info = [x for x in output if x.find(WifiHandler.interface_name) != -1]
            assert len(inter_info) != 0
        except AssertionError as e:
            print(e)
            self.error_and_return("Cannot find wlan0 device interface")
            return
        inter_info = inter_info[0].split(' ')
        
        for data in inter_info:
            if data.find('ESSID') != -1:
                wlan0_info = data.split(':')[1]
                wlan0_info = wlan0_info[1:-1]
        if wlan0_info != 'ff/an':
            wifi_info[0]['SSID'] = wlan0_info
            wifi_info[0]['STATUS'] = True
            
        return wifi_info
    
    def is_wifi_connected(self, current_wifi_info):
        """ True/false whether wifi connected
        """
        return current_wifi_info.get('wifi_status')

    def scan_candidate_wifi(self):
        """ scanning candidate wifi information
        """
        cmd = self.select_cmd('search_wifi_list')

        # scan wifi list
        self.is_inter_up = False
        while True:
            try:
                with Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE) as proc:
                    output = proc.communicate(input=(WifiHandler.sudo_password+'\n').encode())
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
                    print('interface off')
                    return
                else:
                    print('resource busy')
                    pass
            time.sleep(0.01)

        # parsing all ssid list
        ssid_cnt = 0
        tmp_scanned_wifi_info = dict()
        tmp_known_host = []
        for each_line in output[0].decode('utf-8').split('\n'):
            tmp_each_info = []
            if each_line.find('BSS') != -1 and each_line.find(WifiHandler.interface_name) != -1:
                if ssid_cnt != 0 and len(tmp_scanned_wifi_info.get(ssid_cnt)) == 2:
                    tmp_scanned_wifi_info[ssid_cnt].append("FREE")
                ssid_cnt += 1
                tmp_scanned_wifi_info[ssid_cnt] = []
            elif each_line.find('signal') != -1:
                tmp_scanned_wifi_info[ssid_cnt].append(int(float(each_line.split(' ')[1])))
            elif each_line.find('SSID:') != -1:
                tmp_ssid = each_line.split(' ')[1]
                if tmp_ssid != '' and tmp_ssid.find('x00') == -1:
                    is_known_host = self.is_known_host(tmp_ssid)
                    tmp_scanned_wifi_info[ssid_cnt].append(tmp_ssid)
                    tmp_scanned_wifi_info[ssid_cnt].append(is_known_host)
            elif each_line.find('RSN') != -1:
                tmp_scanned_wifi_info[ssid_cnt].append('PSK')
        # Sort out the duplicate value and generate json format 
        df_scanned_wifi_info = pd.DataFrame(data=tmp_scanned_wifi_info.values(),
                                                columns=['SIGNAL', 'SSID', 'KNOWN_HOST', 'PSK'])[['SSID', 'PSK', 'SIGNAL', 'KNOWN_HOST']]
        df_tmp_psk = df_scanned_wifi_info[['SSID', 'PSK', 'KNOWN_HOST']].drop_duplicates()
        df_tmp_signal = df_scanned_wifi_info.groupby('SSID').SIGNAL.min().reset_index(name = "SIGNAL")
        wifi_info = pd.merge(df_tmp_psk, df_tmp_signal, how="inner", on="SSID").sort_values(by=['SIGNAL']).to_dict('records')
        
        return wifi_info

    def is_pi_have_ssid(self, data):

        cmd = self.select_cmd('wpa_list')
        try:
            with Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE) as proc:
                output = proc.communicate(input=(WifiHandler.sudo_password+'\n').encode())
        except SubprocessError as e:
            print(e)
            # self.error_and_return('Improper Popen object opened')
            return
            
        output = output[0].decode('utf-8')
        target_ssid = str(data.get('SSID'))
        target_line = [line for line in output.split('\n') if line.find(target_ssid) != -1]
        print('target_ssid : ', target_ssid)
        print(target_line)
        if not target_line:
            # TODO: Add function to append known_host list
            return -1
        else:
            return int(target_line[0][0])

    def select_network(self, index):
        cmd = self.select_cmd('wpa_select_network')
        cmd.append(str(index))
        print(cmd)
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
            print(wifi_info[0].get('STATUS'))
            if wifi_info[0].get('STATUS'):
                break
            time.sleep(0.01)

        return wifi_info

    def write_wpa(self, data):
        
        ssid = data.get('SSID')
        psk = data.get('PSK')
        cmd_copy = self.select_cmd('copy_wpa_supplicant')
        cmd_chmod = self.select_cmd('change_mode')
        try:
            subprocess.run(cmd_copy)
            subprocess.run(cmd_chmod)
        except SubprocessError as e:
            print(e)
            self.error_and_return('Copy wpa_supplicant error')
            return
        
        cmd_copy_temp = self.select_cmd('copy_temp_wpa_supplicant')
        try:
            subprocess.run(cmd_copy_temp)
        except IOError as e:
            print(e)
            return
        
        # write wifi config to file
        try:
            with open(WifiHandler.user_directory, 'a') as f:
                f.write('\n')
                f.write('network={\n')
                f.write('    ssid="' + ssid + '"\n')
                f.write('    psk="' + psk + '"\n')
                f.write('}\n')
                f.close()
        except IOError as e:
            print(e)
            return

        cmd_replace = self.select_cmd('replace_mv_wpa_supplicant')
        try:
            subprocess.run(cmd_replace)
        except SubprocessError as e:
            print(e)
            self.error_and_return('Replace copy error occur')
            return
        
    def reconfigure_wpa(self):

        cmd = self.select_cmd('interface_reconfigure')
        try:
            with Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE) as proc:
                output = proc.communicate(input=(WifiHandler.sudo_password+'\n').encode())
        except SubprocessError as e:
            print(e)
            self.error_and_return('Copy wpa_supplicant error')
            return

        output = output[0].decode('utf-8')
        return output

    def rewrite_wpa(self):

        cmd_replace_tmp = self.select_cmd('replace_mv_temp_wpa_supplicant')
        try:
            subprocess.run(cmd_replace_tmp)
        except SubprocessError as e:
            print(e)
            self.error_and_return('Replace move error occur')
            return

    def remove_temp_wpa(self):

        cmd = self.select_cmd('replace_mv_wpa_supplicant')
        try:
            subprocess.run(cmd_copy)
        except SubprocessError as e:
            print(e)
            self.error_and_return('remove temp supplicant file error')
            return

    def is_psk_right(self, output):

        if output.find('FAIL') != -1:
            return False

        return True
            
    def is_known_host(self, target_ssid):

        cmd = self.select_cmd('wpa_list')
        try:
            with Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE) as proc:
                output = proc.communicate(input=(WifiHandler.sudo_password+'\n').encode())
        except SubprocessError as e:
            print(e)
            self.error_and_return('Improper Popen object opened')
            return
            
        output = output[0].decode('utf-8')
        target_line = [line for line in output.split('\n') if line.find(target_ssid) != -1]

        if not target_line:
            return False
        return True

    def is_psk_right(self, output):
        
        if output.find('FAIL') != -1:
            return False
        return True
                
class WifiGetter(WifiHandler):
    # return the possible wifi list
    def get(self):
        """ Communication interface with jupyter notebook
        """

        # deteremine the wireless status of raspberry Pi
        whole_wifi_info = self.scan_candidate_wifi()
        if self.is_inter_up:
            current_wifi_info = self.get_current_wifi_info()

            for each_info in whole_wifi_info:
                if each_info.get('SSID') == current_wifi_info[0]['SSID']:
                    current_wifi_info[0]['PSK'] = each_info.get('PSK')
                    current_wifi_info[0]['SIGNAL'] = each_info.get('SIGNAL')

            self.write({
                'status' : 200, 
                'statusText' : 'current wifi information',
                'current_wifi_data' : current_wifi_info,
                'whole_wifi_data' : whole_wifi_info,
            })
        else: 
            self.write({'status' : 200, 'statusText' : 'interface off'})
            
class WifiSetter(WifiHandler):
    
    def put(self):
        
        is_psk_right = False
        try:
            data = json.loads(self.request.body.decode('utf-8'))
        except Exception as e:
            print(e)
            self.error_and_return('Cannot get wifi data')
            return

        target_index = self.is_pi_have_ssid(data)
        # 이미 등록된 와이파이는 wpa_supplicant 를 건들 필요가 없음
        if target_index < 0:
            self.write_wpa(data)
            recon_out = self.reconfigure_wpa()
            # 비밀번호 맞았을 때
            if self.is_psk_right(recon_out):
                target_index = self.is_pi_have_ssid(data)
                current_wifi_info = self.select_network(target_index)

                # remove copied wpa_supplicant file
                self.remove_temp_wpa()
                self.write({
                    'status' : 200,
                    'statusText' : 'Wifi connect success',
                    'data' : current_wifi_info
                })
            # 비밀번호 틀렸을 때
            else:
                time.sleep(10)
                self.rewrite_wpa()
                self.write({
                    'status' : 200,
                    'statusText' : 'Wifi password is wrong'
                })
                print('password wrong')
                return
        else:
            current_wifi_info = self.select_network(target_index)
            self.write({
                'status' : 200,
                'statusText' : 'Wifi connect success',
                'data' : current_wifi_info
            })


        print(current_wifi_info[0])
        print('Wifi has connected')

class InterfaceDown(WifiHandler):

    def get(self):
        
        # shut down network interface
        self.interface_down()

        self.write({
            'status' : 200,
            'statusText' : 'Interface down'
        })

class InterfaceUP(WifiHandler):

    def get(self):

        # Network resource up
        self.interface_up()

        whole_wifi_info = self.scan_candidate_wifi()
        if self.is_inter_up:
            current_wifi_info = self.get_current_wifi_info()

            for each_info in whole_wifi_info:
                if each_info.get('SSID') == current_wifi_info[0]['SSID']:
                    current_wifi_info[0]['PSK'] = each_info.get('PSK')
                    current_wifi_info[0]['SIGNAL'] = each_info.get('SIGNAL')

            self.write({
                'status' : 200, 
                'statusText' : 'current wifi information',
                'current_wifi_data' : current_wifi_info,
                'whole_wifi_data' : whole_wifi_info,
            })    
        
def setup_handlers(nbapp):

    # Wifi Setting
    route_pattern_setting_wifi = ujoin(nbapp.settings['base_url'], '/wifi/setting')
    nbapp.add_handlers('.*', [(route_pattern_setting_wifi, WifiSetter)])

    # Scanning wifi list
    route_pattern_wifi_list = ujoin(nbapp.settings['base_url'], '/wifi/scan')
    nbapp.add_handlers('.*', [(route_pattern_wifi_list, WifiGetter)])

    # Shutdown network interfae
    route_pattern_interface_down = ujoin(nbapp.settings['base_url'], '/wifi/interdown')
    nbapp.add_handlers('.*', [(route_pattern_interface_down, InterfaceDown)])

    # Raise network interface
    route_patter_interface_up = ujoin(nbapp.settings['base_url'], '/wifi/interup')
    nbapp.add_handlers('.*', [(route_patter_interface_up, InterfaceUP)])
