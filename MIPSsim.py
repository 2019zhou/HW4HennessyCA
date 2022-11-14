
import argparse as ap
from mips32 import Instruction, Data

parser = ap.ArgumentParser(description='MIPS 32 Simulator by ZhouZhou')
parser.add_argument('--input', type=str, default='testsample.txt',
                    help="path of input file")
parser.add_argument('--outputsim', type=str, default='simulation.txt',
                    help="path of output file for simulation")
parser.add_argument('--outputdis',  type=str, default='disassembly.txt',
                    help="path of output file for disassembly")
parser.add_argument('--operation',  type=str, default='dis', choices=[
                    'dis_sim', 'dis', 'sim'], help="Disassembly or simulation. The value can be 'dis_sim', 'dis' or 'sim'.")

args = parser.parse_args()
operation = args.operation
PC = 64
inst_byte_size = 4

def dis_assembly():
    global PC
    is_break = False
    with open(args.input, 'r') as file_in:
            with open(args.outputdis, 'wt') as file_out:
                for read_buf in file_in.readlines():
                    read_buf = read_buf.strip()
                    if is_break:
                        write_buf = Data(data_str=read_buf, pc_val=PC)
                    else:
                        write_buf = Instruction(instr_str=read_buf, pc_val=PC)
                        is_break = write_buf.is_break()

                    file_out.write(str(write_buf) + '\n')
                    
                    print(str(write_buf) + '\n')
                    PC += inst_byte_size


def simulation():
    print("Simulation")


if __name__ == "__main__":
    print("This is the MIPS 32 Simulator homework done by ZhouZhou for 2022 Computer Architecture.")
    if operation == 'dis' or operation == 'dis_sim':
        dis_assembly()
    if operation == 'sim' or operation == 'dis_sim':
        simulation()