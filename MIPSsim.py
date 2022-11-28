
import argparse as ap
from mips32 import Instruction, Data
from utils import extract_data, signed_str_to_int, int_to_16bitstr
# from simplesim import SimpleSim
from pipeline import PipeLine

parser = ap.ArgumentParser(description='MIPS 32 Simulator by ZhouZhou')
parser.add_argument('--input', type=str, default='testsample.txt',
                    help="path of input file")
parser.add_argument('--outputfilename', type=str, default='simulation.txt',
                    help="path of output file for simulation")
parser.add_argument('--outputdis',  type=str, default='disassembly.txt',
                    help="path of output file for disassembly")
parser.add_argument('--operation',  type=str, default='dis_sim', choices=[
                    'dis_sim', 'dis', 'sim'], help="Disassembly or simulation. The value can be 'dis_sim' which performs both disassembly and the simulation, 'dis' which performs disassembley or 'sim' which performs simulation")

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
                    
                    # print(str(write_buf) + '\n')
                    PC += inst_byte_size


def simulation():
    instr_mem, data_mem = extract_data(args.input)
    # sim = SimpleSim(instr_mem, data_mem)
    sim = Pipeline(instr_mem, data_mem)
    cycle = 0
    with open(args.outputfilename, 'wt') as file_out:
        while not sim.is_over:
            cycle += 1
            if cycle == 100:
                break
            write_buf = '--------------------\nCycle:{}\t{}\t{}'.format(sim.cycle + 1, 
                                    str(sim.PC), '\t'.join(str(instr_mem[sim.PC].desc_str).split(' ', 1)))
            sim.next_instr()
            write_buf += '\n\n{}\n{}\n'.format(str(sim.RF), str(sim.DS))
            file_out.write(str(write_buf))


if __name__ == "__main__":
    print("This is the MIPS 32 Simulator homework done by ZhouZhou for 2022 Computer Architecture.")
    if operation == 'dis' or operation == 'dis_sim':
        # dis_assembly()   # uncomment this line to perform disassembly
        print("not for assignment 2") 
    if operation == 'sim' or operation == 'dis_sim':
        simulation()