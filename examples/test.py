from param_set import get_var, set_var


def callback(current_list_num, current_edit_var):
    print(current_list_num, current_edit_var)


print(get_var('normal.data1'))
print(get_var('pid.controller1'))
print(get_var('pid.controller1.p'))
print(get_var('pid.controller1.i'))
print(get_var('pid.controller1.d'))
print(get_var('hsv.hsv1'))
set_var('/dev/ttyTHS0', 9600, callback)
