# Homework for Computer Architecture Course

## 说明
### 简单使用: 默认输入为disassembly.txt, 输出为simulation.txt
```shell
python MIPSsim.py 
```
### 指定输入输出文件，指定disassembly 还是 simulation 还是 两个都，默认只执行simulation
```shell
usage: MIPSsim.py [-h] [--input INPUT] [--outputsim OUTPUTSIM]
                  [--outputdis OUTPUTDIS] [--operation {dis_sim,dis,sim}]

MIPS 32 Simulator by ZhouZhou

optional arguments:
  -h, --help            show this help message and exit
  --input INPUT         path of input file
  --outputsim OUTPUTSIM
                        path of output file for simulation
  --outputdis OUTPUTDIS
                        path of output file for disassembly
  --operation {dis_sim,dis,sim}
                        Disassembly or simulation. The value can be 'dis_sim',
                        'dis' or 'sim'.
```

## File

- MIPSsim.py  main file to run the mipssim
- mips32.py    implement the MIPS instructions mainly about disassemble
- utils.py  utils for extract lists and dicts
- simplesim.py simulate the process of running the instructions
- /tests4pipeline/ -- tests to validate the implementation of homework of self-defined scoreboarding algorithm
- /tests4simplesim/ -- tests to validate the implemenation of simple cycles
  - ref_disassembly.txt referenced disassembly file given in hw
  - ref_simulation.txt referenced simuluation file given in hw

## Local Env

- ubuntu 18.04
- python 3.9.16