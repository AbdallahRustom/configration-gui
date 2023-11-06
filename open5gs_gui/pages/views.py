from django.shortcuts import render, redirect
from django.http import HttpResponse
import re
import yaml
import ipaddress
import subprocess
import os
import json
import paramiko

# Create your views here.

def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False
    
def validate_ip_net(value):
    try:
        ip_net = ipaddress.ip_network(value)
        return ip_net
    except ValueError:
        return False

def defaultweb(request): 
    return render(request, 'pages/defaultweb.html')

def success_view(request):
    return render(request, 'pages/success.html')

def ipaddrerror(request):
    return render(request, 'pages/ipaddrerror')

def ipaddrdub(request):
    return render(request, 'pages/ipaddrdub')

def apndub(request):
    return render(request, 'pages/apndub')

def failedtodeploy(request):
    return render(request, 'pages/failedtodeploy')

######################################
##     Handling APN Configration    ##
######################################

def apn (request):
    common_dict={}
    ipv4_dict={}
    ipv6_dict={}
    subnets={}    
    if request.method== 'POST':
        submit_type = request.POST.get('submit_type')
        
        ######################################
        ##  Handling APN Save Configration  ##
        ######################################
        
        if submit_type == 'saveconfig':
            original_working_directory = os.getcwd()
            apn_paramaters=['ADDR','ADDR2','DEV','DNN']
            
            for apn_paramater in apn_paramaters:
                new_paramater= request.POST.get(apn_paramater.lower()) 
                common_dict[apn_paramater.lower()]=new_paramater 
                
                if apn_paramater.lower() == 'addr' or apn_paramater.lower() =='addr2' :
                    subnets[apn_paramater.lower()] = re.search(r"\/(\d{1,3})",new_paramater).group()
                    
                    if validate_ip_net(new_paramater): 
                        validated_ip_net = validate_ip_net(new_paramater)
                        first_addr = next(validated_ip_net.hosts(), None)
                       
                        if not first_addr:
                            return render(request, 'pages/apnconf.html', {'error_message': f"Invalid IP subnet "})
                        
                        else:
                            first_addr = first_addr.exploded
                            common_dict["first_ip_"+apn_paramater.lower()]=first_addr
                    
                    else:
                        return render(request, 'pages/apnconf.html', {'error_message': f"Invalid IP subnet"})   
           
            for key,value in common_dict.items():
                
                if key == 'first_ip_addr' :
                    ipv4_dict['addr']=value + subnets.get('addr')
                
                if key == 'first_ip_addr2':
                    ipv6_dict['addr']=value +subnets.get('addr2')
                
                elif key == 'dev' or key == 'dnn':
                    ipv4_dict[key]=value
                    ipv6_dict[key]=value                
           
            yaml_SMF_file_path = "/home/ubuntu/docker_open5gs/smf/smf.yaml"
            yaml_UPF_file_path = "/home/ubuntu/docker_open5gs/upf/upf.yaml"            
           
            with open(yaml_SMF_file_path, "r") as file:
                data = yaml.safe_load(file)
            
            with open(yaml_UPF_file_path, "r") as file:
                data1 = yaml.safe_load(file)            
            
            keys = ['addr', 'dnn', 'dev']
            duplicate_found = False         
            
            for previous_data_in_yaml in data['smf']['subnet']:
                
                for key in keys: 
                   
                    if ipv4_dict.get(key) == previous_data_in_yaml.get(key) :
                        duplicate_found = True
                        duplicated_value = ipv4_dict.get(key)
                        break
                    
                    elif ipv6_dict.get('addr') == previous_data_in_yaml.get('addr') :
                        duplicate_found = True
                        duplicated_value = ipv6_dict.get('addr')
                        break
            
            for previous_data_in_yaml in data1['upf']['subnet']:
                
                for key in keys: 
                    
                    if ipv4_dict.get(key) == previous_data_in_yaml.get(key) :
                        duplicate_found = True
                        duplicated_value = ipv4_dict.get(key)
                        break
                    
                    elif ipv6_dict.get('addr') == previous_data_in_yaml.get('addr') :
                        duplicate_found = True
                        duplicated_value = ipv6_dict.get('addr')
                        break           
            
            if duplicate_found:
                return render(request, 'pages/apnconf.html', {'error_message': f"Dublication error for {duplicated_value} is already exists"})
            
            else:   
                ipv4_subnet = {'addr': ipv4_dict['addr'],'dnn': ipv4_dict['dnn'],'dev': ipv4_dict['dev']}
                ipv6_subnet = {'addr': ipv6_dict['addr'],'dnn': ipv6_dict['dnn'],'dev': ipv6_dict['dev']}
                common_dict_sub ={'addr': common_dict['addr'],'dnn': common_dict['dnn'],'dev': common_dict['dev'],'addr2': common_dict['addr2']}
                        
                data['smf']['subnet'].append(ipv4_subnet)
                data['smf']['subnet'].append(ipv6_subnet)
                
                with open(yaml_SMF_file_path, 'w') as file:
                    yaml.dump(data, file,default_flow_style=False, sort_keys=False)
                
                data1['upf']['subnet'].append(ipv4_subnet)
                data1['upf']['subnet'].append(ipv6_subnet)
                
                with open(yaml_UPF_file_path, 'w') as file:
                    yaml.dump(data1, file,default_flow_style=False, sort_keys=False)
        
        ##################################################
        ##  Handling APN Save and Restart Configration  ##
        ##################################################
        
        elif submit_type == 'saverestart' :
            original_working_directory = os.getcwd()
            apn_paramaters=['ADDR','ADDR2','DEV','DNN']
            
            for apn_paramater in apn_paramaters:
                new_paramater= request.POST.get(apn_paramater.lower()) 
                common_dict[apn_paramater.lower()]=new_paramater 
                
                if apn_paramater.lower() == 'addr' or apn_paramater.lower() =='addr2' :
                    subnets[apn_paramater.lower()] = re.search(r"\/(\d{1,3})",new_paramater).group()
                    
                    if validate_ip_net(new_paramater): 
                        validated_ip_net = validate_ip_net(new_paramater)
                        first_addr = next(validated_ip_net.hosts(), None)
                        
                        if not first_addr:
                            return render(request, 'pages/apnconf.html', {'error_message': f"Invalid IP subnet "})
                        
                        else:
                            first_addr = first_addr.exploded
                            common_dict["first_ip_"+apn_paramater.lower()]=first_addr
                    
                    else:
                        return render(request, 'pages/apnconf.html', {'error_message': f"Invalid IP subnet"})  
                    
            for key,value in common_dict.items():
                
                if key == 'first_ip_addr' :
                    ipv4_dict['addr']=value + subnets.get('addr')
                
                if key == 'first_ip_addr2':
                    ipv6_dict['addr']=value +subnets.get('addr2')
                
                elif key == 'dev' or key == 'dnn':
                    ipv4_dict[key]=value
                    ipv6_dict[key]=value                
            
            yaml_SMF_file_path = "/home/ubuntu/docker_open5gs/smf/smf.yaml"
            yaml_UPF_file_path = "/home/ubuntu/docker_open5gs/upf/upf.yaml"
            
            with open(yaml_SMF_file_path, "r") as file:
                data = yaml.safe_load(file)
           
            with open(yaml_UPF_file_path, "r") as file:
                data1 = yaml.safe_load(file)  
            
            keys = ['addr', 'dnn', 'dev']
            duplicate_found = False       
            
            for previous_data_in_yaml in data['smf']['subnet']:
                
                for key in keys: 
                    
                    if ipv4_dict.get(key) == previous_data_in_yaml.get(key) :
                        duplicate_found = True
                        duplicated_value = ipv4_dict.get(key)
                        break
                    
                    elif ipv6_dict.get('addr') == previous_data_in_yaml.get('addr') :
                        duplicate_found = True
                        duplicated_value = ipv6_dict.get('addr')
                        break
            
            for previous_data_in_yaml in data1['upf']['subnet']:
                
                for key in keys: 
                
                    if ipv4_dict.get(key) == previous_data_in_yaml.get(key) :
                        duplicate_found = True
                        duplicated_value = ipv4_dict.get(key)
                        break
                
                    elif ipv6_dict.get('addr') == previous_data_in_yaml.get('addr') :
                        duplicate_found = True
                        duplicated_value = ipv6_dict.get('addr')
                        break   
            
            if duplicate_found:
                return render(request, 'pages/apnconf.html', {'error_message': f"Dublication error for {duplicated_value} is already exists"})
            
            else:   
                ipv4_subnet = {'addr': ipv4_dict['addr'],'dnn': ipv4_dict['dnn'],'dev': ipv4_dict['dev']}
                ipv6_subnet = {'addr': ipv6_dict['addr'],'dnn': ipv6_dict['dnn'],'dev': ipv6_dict['dev']}
                common_dict_sub ={'addr': common_dict['addr'],'dnn': common_dict['dnn'],'dev': common_dict['dev'],'addr2': common_dict['addr2']}
                
                data['smf']['subnet'].append(ipv4_subnet)
                data['smf']['subnet'].append(ipv6_subnet)
                
                with open(yaml_SMF_file_path, 'w') as file:
                    yaml.dump(data, file,default_flow_style=False, sort_keys=False)
                
                data1['upf']['subnet'].append(ipv4_subnet)
                data1['upf']['subnet'].append(ipv6_subnet)
                
                with open(yaml_UPF_file_path, 'w') as file:
                    yaml.dump(data1, file,default_flow_style=False, sort_keys=False)
                
                list_of_new_tun = []
                merged_dicts = {}
                
                for listofdict in data1['upf']['subnet']:
                
                    if listofdict['dev'] != 'ogstun' and listofdict['dev'] != 'ogstun2':
                        dnn = listofdict['dnn']
                
                        if dnn not in merged_dicts:
                            merged_dicts[dnn] = listofdict
                
                        else:
                            merged_dicts[dnn]['addr2'] = listofdict['addr']
                
                for d in merged_dicts.values():
                    d['addr'] = str(ipaddress.IPv4Network(d['addr'], strict=False))
    
                    if 'addr2' in d:
                        d['addr2'] = str(ipaddress.IPv6Network(d['addr2'], strict=False))
                list_of_new_tun.extend(merged_dicts.values())                                   
            
            new_working_directory = "/home/ubuntu/docker_open5gs"
            os.chdir(new_working_directory)
            bash_command="docker-compose restart smf upf" 
            bash_command_result = subprocess.run(bash_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if bash_command_result.returncode == 0: 
            
                for no_of_commands in list_of_new_tun:
                    common_dict_sub_str = json.dumps(no_of_commands)
                running_newtunnel_init =subprocess.run(f"docker exec -e COMMON_DICT='{common_dict_sub_str}' upf bash /mnt/upf/new_tunnel.sh", shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            
                if running_newtunnel_init.returncode != 0:
                    os.chdir(original_working_directory)
                    return render(request, 'pages/apnconf.html', {'error_message': f"Deployment failed for SMF and UPF because{running_newtunnel_init.stderr} "})
            
            else:
                os.chdir(original_working_directory)
                return render(request, 'pages/apnconf.html', {'error_message': f"Deployment failed for SMF and UPF because{bash_command_result.stderr} "})
            
        ##################################################
        ##  Handling View Save and Restart Configration ##
        ##################################################    
        elif submit_type == 'viewapn':
            original_working_directory = os.getcwd() 
            yaml_SMF_file_path = "/home/ubuntu/docker_open5gs/smf/smf.yaml"
            
            with open(yaml_SMF_file_path, "r") as file:
                data = yaml.safe_load(file)
            configration_strings = [] 
            
            for apns in data['smf']['subnet']:
                configration_string = ', '.join([f"{key}={value}" for key, value in apns.items()])
                configration_strings.append(configration_string)
            
            configurations = '\n'.join(configration_strings)            
            return render(request, 'pages/apnconf.html',{'error_message': configurations})
        
        ##################################################
        ##      Handling Apply Current Configration     ##
        ################################################## 
        elif submit_type == 'applyconfig':
            original_working_directory = os.getcwd()
            yaml_SMF_file_path = "/home/ubuntu/docker_open5gs/smf/smf.yaml"
        
            with open(yaml_SMF_file_path, "r") as file:
                data = yaml.safe_load(file)
        
            new_working_directory = "/home/ubuntu/docker_open5gs"
            os.chdir(new_working_directory)
            bash_command="docker-compose restart smf"
            bash_command_result = subprocess.run(bash_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
            if bash_command_result.returncode != 0: 
                os.chdir(original_working_directory)
        
                return render(request, 'pages/apnconf.html', {'error_message': f"Deployment failed for SMF and UPF because{bash_command_result.stderr} "})
            yaml_UPF_file_path = "/home/ubuntu/docker_open5gs/upf/upf.yaml"
            ip_dict=[]
        
            with open(yaml_UPF_file_path, "r") as file:
                data1 = yaml.safe_load(file) 
        
            for apndict in data1['upf']['subnet']:
        
                if apndict['dev'] != 'ogstun' and apndict['dev'] != 'ogstun2':
                    ip_dict.append(apndict)
        
            if ip_dict ==[] :
                new_working_directory = "/home/ubuntu/docker_open5gs"
                os.chdir(new_working_directory)
                bash_command="docker-compose restart upf"
                bash_command_result = subprocess.run(bash_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
                if bash_command_result.returncode != 0: 
                    os.chdir(original_working_directory)
                    return render(request, 'pages/apnconf.html', {'error_message': f"Deployment failed for SMF and UPF because{bash_command_result.stderr} "})
        
                elif bash_command_result.returncode != 0:
                    os.chdir(original_working_directory)
                    return render(request, 'pages/apnconf.html',{'error_message': f"Success"})
        
            else : 
                    new_working_directory = "/home/ubuntu/docker_open5gs"
                    grouped_dicts = {}
        
                    for item in ip_dict:
                        dnn = item['dnn']
                        addr = item['addr']
                        dev = item['dev']
                        addr_key = 'addr2' if addr.startswith('2') else 'addr'
                        ip_net = ipaddress.ip_network(addr, strict=False)
                        addr_prefix = str(ip_net.network_address) + '/' + str(ip_net.prefixlen)
        
                        if dnn not in grouped_dicts:
                            grouped_dicts[dnn] = {'dnn': dnn, 'dev': dev, addr_key: addr_prefix}
        
                        else:
                            existing_dict = grouped_dicts[dnn]
                            existing_dict[addr_key] = addr_prefix
        
                    result = list(grouped_dicts.values())
                    bash_command="docker-compose restart upf" 
                    bash_command_result = subprocess.run(bash_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
                    if bash_command_result.returncode == 0: 
        
                        for apn_dict in result:
                            apn_dict_str=json.dumps(apn_dict)
                            running_newtunnel_init =subprocess.run(f"docker exec -e COMMON_DICT='{apn_dict_str}' upf bash /mnt/upf/new_tunnel.sh", shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        
                            if running_newtunnel_init.stderr !=0:
                                return render(request, 'pages/apnconf.html', {'error_message': f"Deployment failed for SMF and UPF because{running_newtunnel_init.stderr}"})               

                    elif bash_command_result.returncode != 0:
                        os.chdir(original_working_directory)
                        return render(request, 'pages/apnconf.html', {'error_message': f"Deployment failed for SMF and UPF because{bash_command_result.stderr}"})   
        
            ################################################
            ##             Handling Delete Apn            ##
            ################################################
        
        elif submit_type == 'deleteapn':
            original_working_directory = os.getcwd()
            apn_delete= request.POST.get('apnname')
            yaml_SMF_file_path = "/home/ubuntu/docker_open5gs/smf/smf.yaml"
            final_apn_list=[]
            tunnel_info_list=[]

            with open(yaml_SMF_file_path, "r") as file:
                data = yaml.safe_load(file)

            for delete_apn_dict in data['smf']['subnet'] :

                if apn_delete not in  delete_apn_dict.values():
                    final_apn_list.append(delete_apn_dict)

                elif apn_delete in delete_apn_dict.values():
                    tunnel_info_list.append(delete_apn_dict)

            if tunnel_info_list != []:        
                data['smf']['subnet'] = final_apn_list  

                with open(yaml_SMF_file_path, "w") as file:
                    yaml.dump(data, file,default_flow_style=False, sort_keys=False)
            else :
                return render(request, 'pages/apnconf.html', {'error_message': f"APN is not configured"})                         

            yaml_UPF_file_path = "/home/ubuntu/docker_open5gs/upf/upf.yaml"

            with open(yaml_UPF_file_path, "r") as file:
                data1 = yaml.safe_load(file)

            if tunnel_info_list != []:
                data1['upf']['subnet'] = final_apn_list

                with open(yaml_UPF_file_path, "w") as file:
                    yaml.dump(data1, file,default_flow_style=False, sort_keys=False)                        

            else :
                return render(request, 'pages/apnconf.html', {'error_message': f"APN is not configured"})
            
            ################################################
            ## Handling Delete and Apn and Restart Service##
            ################################################
        
        elif submit_type == 'deleterestartapn':
            original_working_directory = os.getcwd()
            apn_delete= request.POST.get('apnname')
            yaml_SMF_file_path = "/home/ubuntu/docker_open5gs/smf/smf.yaml"
            final_apn_list=[]
            tunnel_info_list=[]

            with open(yaml_SMF_file_path, "r") as file:
                data = yaml.safe_load(file)

            for delete_apn_dict in data['smf']['subnet'] :

                if apn_delete not in  delete_apn_dict.values():
                    final_apn_list.append(delete_apn_dict)

                elif apn_delete in delete_apn_dict.values():
                    tunnel_info_list.append(delete_apn_dict)

            if tunnel_info_list != []:        
                data['smf']['subnet'] = final_apn_list  

                with open(yaml_SMF_file_path, "w") as file:
                    yaml.dump(data, file,default_flow_style=False, sort_keys=False)

            else :
                return render(request, 'pages/apnconf.html', {'error_message': f"APN is not configured"})                         

            yaml_UPF_file_path = "/home/ubuntu/docker_open5gs/upf/upf.yaml"

            with open(yaml_UPF_file_path, "r") as file:
                data1 = yaml.safe_load(file)

            if tunnel_info_list != []:
                data1['upf']['subnet'] = final_apn_list

                with open(yaml_UPF_file_path, "w") as file:
                    yaml.dump(data1, file,default_flow_style=False, sort_keys=False)         

                for apn_tunnel_dicts in tunnel_info_list :

                    if apn_tunnel_dicts['dev'] != 'ogstun2' or apn_tunnel_dicts['dev'] != 'ogstun':
                        running_newtunnel_init =subprocess.run(f"docker exec upf ip link delete '{apn_tunnel_dicts['dev']}'", shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)               

            else :
                return render(request, 'pages/apnconf.html', {'error_message': f"APN is not configured"})
         
            ################################################
            ##        Handling APN Modififcation          ##
            ################################################
            
        elif submit_type == 'modifiyapn':
            original_working_directory = os.getcwd()
            apn_modify= request.POST.get('modifiedapn')
            yaml_SMF_file_path = "/home/ubuntu/docker_open5gs/smf/smf.yaml"
            yaml_UPF_file_path = "/home/ubuntu/docker_open5gs/upf/upf.yaml"
            final_apn_list=[]
            tunnel_info_list=[]

            with open(yaml_SMF_file_path, "r") as file:
                data = yaml.safe_load(file) 

            for modify_apn_dict in data['smf']['subnet'] :

                if apn_modify not in  modify_apn_dict.values():
                    final_apn_list.append(modify_apn_dict)

                elif apn_modify in modify_apn_dict.values():
                    tunnel_info_list.append(modify_apn_dict)                             

            if tunnel_info_list != [] :   
                mod_keys = ['addr', 'dev','addr2']
                modified_dict={}
                modified_dict['dnn'] = apn_modify

                for key in mod_keys:

                    if request.POST.get(f'modified{key}') != '' :    
                        modified_dict[key] = request.POST.get(f'modified{key}')

                if 'addr' in modified_dict:        

                    if not validate_ip_net(modified_dict['addr']) :
                        return render(request, 'pages/apnconf.html', {'error_message': f"Invalid IP Subnet"}) 

                    for final_apn_list_dict in final_apn_list:
                        validated_net = validate_ip_net(modified_dict['addr'])
                        first_addr = next(validated_net.hosts(), None)
                        first_addr = first_addr.exploded
                        subnet = re.search(r"\/(\d{1,3})",modified_dict['addr']).group()
                        final_addr = first_addr + subnet

                        if final_addr == final_apn_list_dict['addr']:
                            return render(request, 'pages/apnconf.html', {'error_message': f"Duplicated IP Address"}) 

                if 'addr2' in modified_dict : 

                    if not validate_ip_net(modified_dict['addr2']) :
                        return render(request, 'pages/apnconf.html', {'error_message': f"Invalid IP Subnet"})

                    for final_apn_list_dict in final_apn_list:
                        validated_net = validate_ip_net(modified_dict['addr2'])
                        first_addr = next(validated_net.hosts(), None)
                        first_addr = first_addr.exploded
                        subnet = re.search(r"\/(\d{1,3})",modified_dict['addr2']).group()
                        final_addr = first_addr + subnet

                        if final_addr == final_apn_list_dict['addr']:
                            return render(request, 'pages/apnconf.html', {'error_message': f"Duplicated IP Address"})        

                if 'dev' in modified_dict :

                    for final_apn_list_dict in final_apn_list:

                        if modified_dict['dev'] == final_apn_list_dict['dev']:
                            return render(request, 'pages/apnconf.html', {'error_message': f"Duplicated interface"})   

                final_emtpy_list= []

                for index, info_dict in enumerate(tunnel_info_list):
                    empty_dict = {}

                    if index == 0 and  'addr' in modified_dict:
                        validated_ip_net = validate_ip_net(modified_dict['addr'])
                        first_ipv4_addr = next(validated_ip_net.hosts(), None)
                        first_ipv4_addr = first_ipv4_addr.exploded
                        subnet = re.search(r"\/(\d{1,3})",modified_dict['addr']).group()
                        final_ipv4_addr = first_ipv4_addr + subnet                        
                        empty_dict['addr'] = final_ipv4_addr

                    else:
                        empty_dict['addr'] = info_dict['addr']

                    if index == 1 and 'addr2' in modified_dict:
                        validated_ip_net = validate_ip_net(modified_dict['addr2'])
                        first_ipv6_addr = next(validated_ip_net.hosts(), None)
                        first_ipv6_addr = first_ipv6_addr.exploded
                        subnet = re.search(r"\/(\d{1,3})",modified_dict['addr2']).group()
                        final_ipv6_addr = first_ipv6_addr + subnet                        
                        empty_dict['addr'] = final_ipv6_addr  
                    empty_dict['dnn'] = apn_modify   

                    if 'dev' in modified_dict:
                        empty_dict['dev'] = modified_dict['dev']

                    else:
                        empty_dict['dev'] = info_dict['dev']                   

                    final_emtpy_list.append(empty_dict)

                modified_data = final_apn_list + final_emtpy_list
                data['smf']['subnet'] = modified_data 

                with open(yaml_SMF_file_path, "w") as file:
                    yaml.dump(data, file,default_flow_style=False, sort_keys=False)
                    
                with open(yaml_UPF_file_path, "r") as file:
                    data1 = yaml.safe_load(file) 

                data1['upf']['subnet'] = modified_data 

                with open(yaml_UPF_file_path, "w") as file:
                    yaml.dump(data1, file,default_flow_style=False, sort_keys=False)

            else :
                return render(request, 'pages/apnconf.html', {'error_message': f"APN is not configured"}) 
            
            #########################################################
            ##        Handling APN Modififcation And Save          ##
            #########################################################
        
        elif submit_type == 'modifiysaveapn':
            original_working_directory = os.getcwd()
            apn_modify= request.POST.get('modifiedapn')
            yaml_SMF_file_path = "/home/ubuntu/docker_open5gs/smf/smf.yaml"
            yaml_UPF_file_path = "/home/ubuntu/docker_open5gs/upf/upf.yaml"
            final_apn_list=[]
            tunnel_info_list=[]

            with open(yaml_SMF_file_path, "r") as file:
                data = yaml.safe_load(file) 

            for modify_apn_dict in data['smf']['subnet'] :

                if apn_modify not in  modify_apn_dict.values():
                    final_apn_list.append(modify_apn_dict)

                elif apn_modify in modify_apn_dict.values():
                    tunnel_info_list.append(modify_apn_dict)                             

            if tunnel_info_list != [] :   
                mod_keys = ['addr', 'dev','addr2']
                modified_dict={}
                modified_dict['dnn'] = apn_modify

                for key in mod_keys:

                    if request.POST.get(f'modified{key}') != '' :    
                        modified_dict[key] = request.POST.get(f'modified{key}')

                if 'addr' in modified_dict:        

                    if not validate_ip_net(modified_dict['addr']) :
                        return render(request, 'pages/apnconf.html', {'error_message': f"Invalid IP Subnet"}) 

                    for final_apn_list_dict in final_apn_list:
                        validated_net = validate_ip_net(modified_dict['addr'])
                        first_addr = next(validated_net.hosts(), None)
                        first_addr = first_addr.exploded
                        subnet = re.search(r"\/(\d{1,3})",modified_dict['addr']).group()
                        final_addr = first_addr + subnet

                        if final_addr == final_apn_list_dict['addr']:
                            return render(request, 'pages/apnconf.html', {'error_message': f"Duplicated IP Address"}) 

                if 'addr2' in modified_dict : 

                    if not validate_ip_net(modified_dict['addr2']) :
                        return render(request, 'pages/apnconf.html', {'error_message': f"Invalid IP Subnet"})

                    for final_apn_list_dict in final_apn_list:
                        validated_net = validate_ip_net(modified_dict['addr2'])
                        first_addr = next(validated_net.hosts(), None)
                        first_addr = first_addr.exploded
                        subnet = re.search(r"\/(\d{1,3})",modified_dict['addr2']).group()
                        final_addr = first_addr + subnet

                        if final_addr == final_apn_list_dict['addr']:
                            return render(request, 'pages/apnconf.html', {'error_message': f"Duplicated IP Address"})        

                if 'dev' in modified_dict :

                    for final_apn_list_dict in final_apn_list:

                        if modified_dict['dev'] == final_apn_list_dict['dev']:
                            return render(request, 'pages/apnconf.html', {'error_message': f"Duplicated interface"})         

                final_emtpy_list= []

                for index, info_dict in enumerate(tunnel_info_list):
                    empty_dict = {}

                    if index == 0 and  'addr' in modified_dict:
                        validated_ip_net = validate_ip_net(modified_dict['addr'])
                        first_ipv4_addr = next(validated_ip_net.hosts(), None)
                        first_ipv4_addr = first_ipv4_addr.exploded
                        subnet = re.search(r"\/(\d{1,3})",modified_dict['addr']).group()
                        final_ipv4_addr = first_ipv4_addr + subnet                        
                        empty_dict['addr'] = final_ipv4_addr

                    else:
                        empty_dict['addr'] = info_dict['addr']

                    if index == 1 and 'addr2' in modified_dict:
                        validated_ip_net = validate_ip_net(modified_dict['addr2'])
                        first_ipv6_addr = next(validated_ip_net.hosts(), None)
                        first_ipv6_addr = first_ipv6_addr.exploded
                        subnet = re.search(r"\/(\d{1,3})",modified_dict['addr2']).group()
                        final_ipv6_addr = first_ipv6_addr + subnet                        
                        empty_dict['addr'] = final_ipv6_addr  
                        
                    empty_dict['dnn'] = apn_modify   
                    
                    if 'dev' in modified_dict:
                        empty_dict['dev'] = modified_dict['dev']
                    
                    else:
                        empty_dict['dev'] = info_dict['dev']                   
                    
                    final_emtpy_list.append(empty_dict)
                    
                modified_data = final_apn_list + final_emtpy_list
                data['smf']['subnet'] = modified_data 
                
                with open(yaml_SMF_file_path, "w") as file:
                    yaml.dump(data, file,default_flow_style=False, sort_keys=False)
                    
                with open(yaml_UPF_file_path, "r") as file:
                    data1 = yaml.safe_load(file) 
                
                data1['upf']['subnet'] = modified_data 
                
                with open(yaml_UPF_file_path, "w") as file:
                    yaml.dump(data1, file,default_flow_style=False, sort_keys=False)
                    
                original_working_directory = os.getcwd()    
                new_working_directory = "/home/ubuntu/docker_open5gs"
                os.chdir(new_working_directory)
                bash_command="docker-compose restart upf smf"
                bash_command_result = subprocess.run(bash_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                if bash_command_result.stderr  :
                    
                    list_of_new_tun = []
                    merged_dicts = {}
                
                    for each_dic in modified_data:
                        if each_dic['dev'] != 'ogstun' and each_dic['dev'] != 'ogstun2':
                            dnn = each_dic['dnn']
                    
                            if dnn not in merged_dicts:
                                merged_dicts[dnn] = each_dic
                    
                            else:
                                merged_dicts[dnn]['addr2'] = each_dic['addr']
                    
                    for d in merged_dicts.values():
                        d['addr'] = str(ipaddress.IPv4Network(d['addr'], strict=False))
        
                        if 'addr2' in d:
                            d['addr2'] = str(ipaddress.IPv6Network(d['addr2'], strict=False))
                    list_of_new_tun.extend(merged_dicts.values())                                        

                    for each_dict_final in list_of_new_tun :
                            each_dict_final_str=json.dumps(each_dict_final)
                            running_newtunnel_init =subprocess.run(f"docker exec -e COMMON_DICT='{each_dict_final_str}' upf bash /mnt/upf/new_tunnel.sh", shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)

                            if running_newtunnel_init.stderr !=0:
                                os.chdir(original_working_directory)
                                return render(request, 'pages/apnconf.html', {'error_message': f"failed for UPF because {running_newtunnel_init.stderr}"})               

            else :
                return render(request, 'pages/apnconf.html', {'error_message': f"APN is not configured"})    

        os.chdir(original_working_directory)
        return render(request, 'pages/apnconf.html',{'error_message': f"Success"})        

    return render(request, 'pages/apnconf.html')

######################################
## Handling ENVIROMENT Configration ##
######################################

def env (request):
    if request.method== 'POST':
        submit_type = request.POST.get('submit_type')
        
        ##########################################################
        ##  Handling ENVIROMENT Configration Save Configration  ##
        ##########################################################
        
        if submit_type == 'saveconfig':
        
            new_mcc=request.POST.get('mcc')
            new_mnc=request.POST.get('mnc')
            mcc_line_regex = r"MCC=(\d{3})"
            mnc_line_regex = r"MNC=(\d{2})"
            ip_variables = ['MME_IP','MONGO_IP','HSS_IP','PCRF_IP','SGWC_IP','SGWU_IP','SGWU_ADVERTISE_IP','SMF_IP','UPF_IP','UPF_ADVERTISE_IP']
            
            previous_env_ip_list=[]
            env_path = "/home/ubuntu/docker_open5gs/.env"
            
            with open(env_path, "r") as file:
                data = file.read()  
                data = re.sub(mcc_line_regex,f"MCC={new_mcc}", data)
                data = re.sub(mnc_line_regex,f"MNC={new_mnc}", data)        
            
            for previous_env_ip_variable in ip_variables:
                previous_env_ip_match = re.search(rf"^{previous_env_ip_variable}=(\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}})$", data, flags=re.MULTILINE)
                previous_env_ip = previous_env_ip_match.group(1)
                previous_env_ip_list.append(previous_env_ip)
                        
            for ip_variable in ip_variables:
                new_ip= request.POST.get(ip_variable.lower())
                
                if is_valid_ip(new_ip) is False:
                    return render(request, 'pages/env.html', {'error_message': f"Invalid IP address for {ip_variable}"})
                
                elif new_ip in previous_env_ip_list:
                    return render(request, 'pages/env.html', {'error_message': f"IP address is Duplicated for {ip_variable}"})
                                
                ip_line_regex = rf"^{ip_variable}=\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}$"
                data = re.sub(ip_line_regex, f"{ip_variable}={new_ip}", data, flags=re.MULTILINE)
                                                        
            with open(env_path, "w") as file:
                file.write(data)
                
        ##############################################################################
        ##  Handling ENVIROMENT Configration Save Configration and Restart Service  ##
        ##############################################################################
        
        elif submit_type == 'saverestart':
             
            new_mcc=request.POST.get('mcc')
            new_mnc=request.POST.get('mnc')
            mcc_line_regex = r"MCC=(\d{3})"
            mnc_line_regex = r"MNC=(\d{2})"
            ip_variables = ['MME_IP','MONGO_IP','HSS_IP','PCRF_IP','SGWC_IP','SGWU_IP','SGWU_ADVERTISE_IP','SMF_IP','UPF_IP','UPF_ADVERTISE_IP']
            
            previous_env_ip_list=[]
            env_path = "/home/ubuntu/docker_open5gs/.env"
            
            with open(env_path, "r") as file:
                data = file.read()  
                data = re.sub(mcc_line_regex,f"MCC={new_mcc}", data)
                data = re.sub(mnc_line_regex,f"MNC={new_mnc}", data)        
            
            for previous_env_ip_variable in ip_variables:
                previous_env_ip_match = re.search(rf"^{previous_env_ip_variable}=(\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}})$", data, flags=re.MULTILINE)
                previous_env_ip = previous_env_ip_match.group(1)
                previous_env_ip_list.append(previous_env_ip)
                        
            for ip_variable in ip_variables:
                new_ip= request.POST.get(ip_variable.lower())
                
                if is_valid_ip(new_ip) is False:
                    return render(request, 'pages/env.html', {'error_message': f"Invalid IP address for {ip_variable}"})

                elif new_ip in previous_env_ip_list:
                    return render(request, 'pages/env.html', {'error_message': f"IP address is Duplicated for {ip_variable}"})               

                ip_line_regex = rf"^{ip_variable}=\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}\.\d{{1,3}}$"
                data = re.sub(ip_line_regex, f"{ip_variable}={new_ip}", data, flags=re.MULTILINE)                                     

            with open(env_path, "w") as file:
                file.write(data)
                
            original_working_directory = os.getcwd() 
            new_working_directory = "/home/ubuntu/docker_open5gs"
            os.chdir(new_working_directory)
            bash_command_down="docker-compose down"
            bash_command_down_result = subprocess.run(bash_command_down, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
           
            if bash_command_down_result.returncode == 0:
                bash_command_up="docker-compose up -d "
                bash_command_up_result = subprocess.run(bash_command_up, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                os.chdir(original_working_directory)

                if bash_command_up_result.returncode != 0:
                    os.chdir(original_working_directory)
                    return render(request, 'pages/env.html', {'error_message': f"Deployment failed for SMF and UPF because{bash_command_up_result.stderr} "})            

            else:
                os.chdir(original_working_directory)
                return render(request, 'pages/env.html', {'error_message': f"Deployment failed for SMF and UPF because{bash_command_down_result.stderr} "})
        
        ##########################################################
        ##         Handling View ENVIROMENT Configration        ##
        ##########################################################
        
        elif submit_type == 'viewenv':
            print('Hello')
            env_path = "/home/ubuntu/docker_open5gs/.env"

            with open(env_path, "r") as file:
                data = file.read()  

            return render(request, 'pages/env.html', {'error_message': f"{data}"})
        
        ##########################################################################
        ##         Handling  ENVIROMENT Configration Apply Current Config       ##
        ##########################################################################
        
        
        elif submit_type == 'applyenv':
            original_working_directory = os.getcwd() 
            new_working_directory = "/home/ubuntu/docker_open5gs"
            os.chdir(new_working_directory)
            bash_command_down="docker-compose down"
            bash_command_down_result = subprocess.run(bash_command_down, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
           
            if bash_command_down_result.returncode == 0:
                bash_command_up="docker-compose up -d "
                bash_command_up_result = subprocess.run(bash_command_up, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                os.chdir(original_working_directory)

                if bash_command_up_result.returncode != 0:
                    os.chdir(original_working_directory)
                    return render(request, 'pages/env.html', {'error_message': f"Deployment failed for SMF and UPF because{bash_command_up_result.stderr} "})            

            else:
                os.chdir(original_working_directory)
                return render(request, 'pages/env.html', {'error_message': f"Deployment failed for SMF and UPF because{bash_command_down_result.stderr} "})               
        
        return render(request, 'pages/env.html', {'error_message': f"Success"})
    return render(request, 'pages/env.html')


##################################
##         Handling  CDR        ##
##################################

# def cdr (request):
    
#     if request.method== 'POST':
#         submit_type = request.POST.get('submit_type')
                 
#         hostname = '10.1.1.16'
#         port = 2524  
#         username = 'sftpuser'
#         password = 'sftpuser'
#         source_directory = '/open5gs/install/var/log/open5gs'
#         destination_directory = '/home/ubuntu/configration-gui/open5gs_gui/CDR_Logs'

#         try:
#             transport = paramiko.Transport((hostname, port))
#             transport.connect(username=username, password=password)
#             ssh = transport.open_session()
#             ssh.invoke_subsystem('sftp')
#             sftp = paramiko.SFTP.from_transport(transport)

#         except paramiko.AuthenticationException:
#             print("Authentication failed. Please check your credentials.")
#             return render(request, 'pages/cdr.html', {'error_message': f"Authentication failed. Please check your credentials."})               
            
#         except paramiko.SSHException as e:
#             print(f"SSH connection failed: {str(e)}")
#             return render(request, 'pages/cdr.html', {'error_message': f"SSH connection failed: {str(e)}"})               

#         try:
#             sftp.chdir(source_directory)
        
#         except FileNotFoundError:
#             print(f"Source directory '{source_directory}' does not exist on the server.")
#             return render(request, 'pages/cdr.html', {'error_message': f"Source directory '{source_directory}' does not exist on the server."})               

#         # List all files in the source directory
#         files = sftp.listdir()
        
#         if submit_type == 'viewcdr': 
#             files_final=[]
#             for file_name in files:
                
#                 if not file_name.endswith('.log'):
#                     files_final.append(file_name) 
                        
#             return render(request, 'pages/cdr.html', {'error_message': f"{files_final}"})  
        
#         if submit_type == 'deletecdr': 
#             cdr_name=request.POST.get('CDR')
            
#             if cdr_name in files:
#                 sftp.chdir(source_directory)
                
#                 try:
#                     sftp.remove(cdr_name)
                
#                 except Exception as e:
#                     return render(request, 'pages/cdr.html', {'error_message': f"Failed to delete '{cdr_name}': {str(e)}"})
                
#             else :
#                 return render(request, 'pages/cdr.html', {'error_message': f"CDR Does not Exist"})      
                      
#         if submit_type == 'getcdr': 
#             for file_name in files:
                
#                 if not file_name.endswith('.log'):
#                     source_path = os.path.join(source_directory, file_name)
#                     destination_path = os.path.join(destination_directory, file_name)
                    
#                     try:
#                         sftp.get(source_path, destination_path)
                    
#                     except Exception as e:
#                         return render(request, 'pages/cdr.html', {'error_message': f"Failed to copy '{file_name}': {str(e)}"})               

#             sftp.close()
#             transport.close()
                
#         return render(request, 'pages/cdr.html', {'error_message': f"Success"})
           
#     return render(request, 'pages/cdr.html')

    

   
    





