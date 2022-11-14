# Homework for Computer Architecture Course

## Usage

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
- /tests/ -- tests to validate the implementation of homework instructions
- ref_disassembly.txt referenced disassembly file given in hw
- ref_simulation.txt referenced simuluation file given in hw