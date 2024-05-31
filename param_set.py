import time
import serial
import yaml


def __read_yaml(file_path):
    with open(file_path, 'r', encoding='gb2312') as file:
        data = yaml.safe_load(file)
    return data


def __open_serial_port(port, baudrate):
    return serial.Serial(port, baudrate, timeout=0.1)


def __write(str):
    global ser
    ser.write(str.encode("gb2312"))
    ser.write(bytes.fromhex('ff ff ff'))


def __root_page():
    global __yaml_data, ser, current_root_page
    __write('page 0')
    try:
        list_len = len(__yaml_data['root']['children'])
    except Exception as e:
        list_len = 0
    if current_root_page == 0:
        __write('vis b4,0')
    if list_len - current_root_page * 4 <= 4:
        __write('vis b5,0')
    if current_root_page == list_len // 4:
        for i in range(list_len % 4, 4):
            __write(f'vis b{i},0')
    for i in range(0, 4):
        if i + current_root_page * 4 >= list_len:
            break
        __write(f'b{i}.txt="{__yaml_data["root"]["children"][i + current_root_page * 4]["name"]}"')


def __list_page():
    global __yaml_data, ser, current_list_page, current_list_num
    __write('page 1')
    try:
        list_len = len(__yaml_data['root']['children'][current_list_num]['children'])
    except Exception as e:
        list_len = 0
    __write('t0.txt="{}"'.format(__yaml_data['root']['children'][current_list_num]['name']))
    if current_list_page == 0:
        __write('vis b2,0')
    if list_len - current_list_page * 5 <= 5:
        __write('vis b3,0')
    for i in range(0, 5):
        if i + current_list_page * 5 >= list_len:
            break
        edit_data = __yaml_data["root"]["children"][current_list_num]["children"][i + current_list_page * 5]
        __write(f't{i * 2 + 1}.txt="{edit_data["name"]}"')
        if edit_data['type'] == 'number':
            __write(f't{i * 2 + 2}.txt="{edit_data["value"]}"')
        elif edit_data['type'] == 'pid':
            try:
                __write(
                    f't{i * 2 + 2}.txt="{edit_data["values"]["p"]},{edit_data["values"]["i"]},{edit_data["values"]["d"]}"')
            except Exception as e:
                __write(f't{i * 2 + 2}.txt="0,0,0"')
        elif edit_data['type'] == 'hsv':
            try:
                __write(
                    f't{i * 2 + 2}.txt="{edit_data["values"]["h"]},{edit_data["values"]["s"]},{edit_data["values"]["v"]}"')
            except Exception as e:
                __write(f't{i * 2 + 2}.txt="0,0,0"')


def __edit_data_page():
    global __yaml_data, ser, current_list_num, current_edit_var
    __write('page 4')
    edit_data = __yaml_data['root']['children'][current_list_num]['children'][current_edit_var]
    __write(f't0.txt="{edit_data["name"]}"')
    try:
        __write(f't1.txt="{edit_data["value"]}"')
    except Exception as e:
        __write(f't1.txt="0"')


def __edit_pid_data_page():
    global __yaml_data, current_list_num, current_edit_var
    __write('page 2')
    try:
        data = __yaml_data['root']['children'][current_list_num]['children'][current_edit_var]['values']
    except Exception as e:
        data = {'p': 0, 'i': 0, 'd': 0}
    __write(f't0.txt="{__yaml_data["root"]["children"][current_list_num]["children"][current_edit_var]["name"]}"')
    __write(f't4.txt="{data["p"]}"')
    __write(f't5.txt="{data["i"]}"')
    __write(f't6.txt="{data["d"]}"')


def __edit_hsv_data_page():
    global __yaml_data, current_list_num, current_edit_var
    __write('page 3')
    try:
        data = __yaml_data['root']['children'][current_list_num]['children'][current_edit_var]['values']
    except Exception as e:
        data = {'h': 0, 's': 0, 'v': 0}
    __write(f't0.txt="{__yaml_data["root"]["children"][current_list_num]["children"][current_edit_var]["name"]}"')
    __write(f't4.txt="{data["h"]}"')
    __write(f't5.txt="{data["s"]}"')
    __write(f't6.txt="{data["v"]}"')


def __save_data():
    global __yaml_data, current_list_num, current_edit_var, __callback
    with open('data.yaml', 'w', encoding='gb2312') as file:
        yaml.dump(__yaml_data, file, default_flow_style=False, allow_unicode=True)
    __callback(__yaml_data['root']['children'][current_list_num]['internal_name'],
               __yaml_data['root']['children'][current_list_num]['children'][current_edit_var]['internal_name'])


def get_var(var_name):
    current_yaml_data = __read_yaml('data.yaml')["root"]["children"]
    var_path = var_name.split('.')
    try:
        for i in range(len(current_yaml_data)):
            if current_yaml_data[i]["internal_name"] == var_path[0]:
                current_yaml_data = current_yaml_data[i]["children"]
                for j in range(len(current_yaml_data)):
                    if len(var_path) == 2:
                        if current_yaml_data[j]["internal_name"] == var_path[1]:
                            if current_yaml_data[j]["type"] == "number":
                                return current_yaml_data[j]["value"]
                            elif current_yaml_data[j]["type"] in ["pid", "hsv"]:
                                return current_yaml_data[j]["values"]
                    elif len(var_path) == 3:
                        if current_yaml_data[j]["internal_name"] == var_path[1]:
                            return current_yaml_data[j]["values"][var_path[2]]
    except Exception as e:
        pass
    return None


def set_var(port, baudrate, callback):
    global current_root_page, current_list_page, current_list_num, current_edit_var, ser, __callback
    ser = __open_serial_port(port, baudrate)
    __callback = callback
    __write('rest')
    time.sleep(0.5)
    current_root_page = 0
    current_list_page = 0
    current_list_num = 0
    current_edit_var = 0
    __root_page()
    mode = 0
    while True:
        try:
            if ser.in_waiting > 0:
                receive = ser.readline().decode('gb2312').strip()
                if mode == 0:
                    if receive == 'pgup':
                        current_root_page -= 1
                        if current_root_page < 0:
                            current_root_page = 0
                        __root_page()
                    elif receive == 'pgdn':
                        current_root_page += 1
                        if current_root_page > len(__yaml_data['root']['children']) // 4:
                            current_root_page = len(__yaml_data['root']['children']) // 4
                        __root_page()
                    elif receive in ['l0', 'l1', 'l2', 'l3']:
                        current_list_num = current_root_page * 4 + int(receive[1])
                        current_list_page = 0
                        mode = 1
                        __list_page()
                if mode == 1:
                    if receive == 'pgup':
                        current_list_page -= 1
                        if current_list_page < 0:
                            current_list_page = 0
                        __list_page()
                    elif receive == 'pgdn':
                        current_list_page += 1
                        if current_list_page > len(__yaml_data['root']['children'][current_list_num]['children']) // 5:
                            current_list_page = len(__yaml_data['root']['children'][current_list_num]['children']) // 5
                        __list_page()
                    elif receive == 'back':
                        mode = 0
                        __root_page()
                    elif receive in ['t0', 't1', 't2', 't3', 't4']:
                        current_edit_var = current_list_page * 5 + int(receive[1])
                        if __yaml_data['root']['children'][current_list_num]['children'][current_edit_var][
                            'type'] == 'number':
                            mode = 2
                            __edit_data_page()
                        elif __yaml_data['root']['children'][current_list_num]['children'][current_edit_var][
                            'type'] == 'pid':
                            mode = 3
                            __edit_pid_data_page()
                        elif __yaml_data['root']['children'][current_list_num]['children'][current_edit_var][
                            'type'] == 'hsv':
                            mode = 4
                            __edit_hsv_data_page()
                if mode == 2:
                    if receive.startswith('back='):
                        __yaml_data['root']['children'][current_list_num]['children'][current_edit_var]['value'] = eval(
                            receive.split('=')[1])
                        mode = 1
                        __save_data()
                        __list_page()
                if mode == 3:
                    if receive.startswith('back='):
                        pid_data = receive.split('=')[1].split(',')
                        __yaml_data['root']['children'][current_list_num]['children'][current_edit_var]['values'] = {
                            'p': int(pid_data[0]), 'i': int(pid_data[1]), 'd': int(pid_data[2])}
                        mode = 1
                        __save_data()
                        __list_page()
                if mode == 4:
                    if receive.startswith('back='):
                        hsv_data = receive.split('=')[1].split(',')
                        __yaml_data['root']['children'][current_list_num]['children'][current_edit_var]['values'] = {
                            'h': int(hsv_data[0]), 's': int(hsv_data[1]), 'v': int(hsv_data[2])}
                        mode = 1
                        __save_data()
                        __list_page()
        except Exception as e:
            pass


__yaml_data = __read_yaml('data.yaml')
__callback = None
