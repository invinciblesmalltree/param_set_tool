# param_set_tool
嵌入式设备调参工具，适用于电赛验收前的实地调参。
# 前置准备
这是一个调参库，只提供 api 库，需要你自己基于 api 实现参数的实际应用过程。  
本工具运行在 TJC3224T124_011 串口屏上，请烧入 HMI 下的串口屏程序以搭配使用。其它型号串口屏请自行修改 USART HMI 程序源码。  
请保证上位机有 python3 环境，并安装好 `pyserial` 和 `pyyaml` 库。
## 安装方式
```bash
pip3 install pyserial pyyaml
```
请确保工作目录下有一个可用的 data.yaml 配置文件并且严格按照 example 中的方法配置。  
本工具不支持嵌套列表，且列表 type 必须为 list ，参数 type 只能是`number`, `pid`, `hsv`，请严格遵守该规定编写 data.yaml
# 使用方法
## 进入设置参数模式
```py
from param_set import set_var


def callback(current_list_name, current_edit_var_name): # 回调函数，可以在这里加入应用更新参数的代码。返回列表名和参数名。
    print(current_list_name, current_edit_var_name)


set_var('/dev/ttyTHS0', 9600, callback)
```
串口屏上点击返回后，配置文件会自动保存至 data.yaml
## 进入获取参数模式
假设 data.yaml 文件
```yaml
root:
  type: list
  name: 参数列表
  children:
    - type: list
      name: 普通参数
      internal_name: normal
      children:
        - type: number
          name: 参数1
          internal_name: data1
          value: 10
        - type: number
    - type: list
      name: pid参数
      internal_name: pid
      children:
        - type: pid
          name: 水平速度pid
          internal_name: controller1
          values:
            p: 10
            i: 10
            d: 10
    - type: list
      name: HSV参数
      internal_name: hsv
      children:
        - type: hsv
          name: 下限hsv
          internal_name: hsv1
          values:
            h: 10
            s: 10
            v: 10
...
```
```py
from param_set import get_var


print(get_var('normal.data1'))
print(get_var('pid.controller1'))
print(get_var('pid.controller1.p'))
print(get_var('pid.controller1.i'))
print(get_var('pid.controller1.d'))
print(get_var('hsv.hsv1'))
```
输出结果
```bash
666
{'d': 30, 'i': 20, 'p': 10}
10
20
30
{'h': 100, 's': 255, 'v': 10}
```
