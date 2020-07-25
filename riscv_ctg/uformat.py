from constraint import *
import random
import re
from riscv_ctg.constants import *

def uformat_opcomb(cgf, randomization):
    rd_picked = []
    op_comb = []
    if 'rd' in cgf:
        rd_range = cgf['rd']
    else:
        rd_range = ['x'+str(random.randint(1,31))]
    variables = ['rd']

    combination_num = len(rd_range)
    rd_picked = []

    for i in range(combination_num):
        if randomization:
            problem = Problem(MinConflictsSolver())
        else:
            problem = Problem()

        problem.addVariable('rd',  rd_range)

        def opconstraint(rd=0):
            if rd not in rd_picked:
                return True

        problem.addConstraint(opconstraint, variables)

        count = 0
        solution = problem.getSolution()
        while (solution is None and count < 5):
            solution = problem.getSolution()
            count = count + 1
        if solution is None:
            print("Can't find a solution - 1")
            exit(0)

        op_tuple = []
        op_tuple.append(solution['rd'])
        op_comb.append( tuple(op_tuple) )
        rd_picked.append(solution['rd'])
        problem.reset()

    if 'op_comb' in cgf:
        rd_range = default_regset.copy()

        for req_op_comb in cgf['op_comb']:
            satisfied = False
            for comb in op_comb:
                rd = comb[0]
                if eval(req_op_comb):
                    satisfied = True
                    break;
            if not satisfied:
                if randomization:
                    problem = Problem(MinConflictsSolver())
                else:
                    problem = Problem()
                problem.addVariable('rd', rd_range)
                problem.addConstraint(lambda rd: eval(req_op_comb) ,\
                        tuple(variables))
                count = 0
                solution = problem.getSolution()
                while (solution is None and count < 5):
                    solution = problem.getSolution()
                    count = count + 1
                if solution is None:
                    print("Can't find a solution - 2")
                    exit(0)
                op_tuple = []
                op_tuple.append(solution['rd'])
                op_comb.append( tuple(op_tuple) )
                problem.reset()
    return op_comb

def uformat_valcomb(cgf,op_node,randomization):
    val_comb = []
    imm_val_data = eval(op_node['imm_val_data'])
    for req_val_comb in cgf['val_comb']:
        if randomization:
            problem = Problem(MinConflictsSolver())
        else:
            problem = Problem(RecursiveBacktrackingSolver())
        problem.addVariables(['imm_val'], imm_val_data)
        problem.addConstraint(lambda imm_val: eval(req_val_comb) ,\
                        ['imm_val'])
        solution = problem.getSolution()
        count = 0
        while (solution is None and count < 5):
            solution = problem.getSolution()
            count = count + 1
        if solution is None:
            print("Can't find a solution - 3")
            exit(0)
        val_comb.append(tuple([str(solution['imm_val'])]))
        problem.reset()
    return val_comb

def uformat_inst(op_comb, val_comb, cgf,op_node):

    instr_dict = []
    imm_val_data = eval(op_node['imm_val_data'])
    cont = []
    if len(op_comb) >= len(val_comb):
        for i in range(len(op_comb)):
            instr = {}
            instr['inst'] = cgf['opcode']
            instr['rd'] = op_comb[i][0]
            if i < len(val_comb):
                instr['imm_val'] = val_comb[i][0]
                if instr['rd'] == 'x0':
                    cont.append(val_comb[i])
            elif cont:
                if instr['rd'] == 'x0':
                    instr['imm_val'] = str(random.choice(imm_val_data))
                else:
                    temp = cont.pop()
                    instr['imm_val'] = temp[0]
            else:
                instr['imm_val'] = str(random.choice(imm_val_data))
            instr_dict.append(instr)
    else:
        for i in range(len(val_comb)):
            instr = {}
            instr['inst'] = cgf['opcode']
            if i < len(op_comb):
                instr['rd'] = op_comb[i][0]

                if instr['rd'] == 'x0':
                    cont.append(val_comb[i])
            else:
                instr['rd'] =  'x' + str(random.randint(1,31))
            instr['imm_val'] = val_comb[i][0]
            instr_dict.append(instr)
    for entry in cont:
            instr = {}
            instr['inst'] = cgf['opcode']
            instr['rd'] =  'x' + str(random.randint(1,31))
            instr['imm_val'] = entry[0]
            instr_dict.append(instr)
    return instr_dict

def uformat_swreg(instr_dict):
    total_instr = len(instr_dict)
    available_reg = default_regset.copy()
    available_reg.remove('x0')
    count = 0
    assigned = 0
    offset = 0
    for instr in instr_dict:
        if instr['rd'] in available_reg:
            available_reg.remove(instr['rd'])

        if len(available_reg) <= 3:
            curr_swreg = available_reg[0]
            offset = 0
            for i in range(assigned, count+1):
                if 'swreg' not in instr_dict[i]:
                    instr_dict[i]['swreg'] = curr_swreg
                    instr_dict[i]['offset'] = str(offset)
                    offset += 4
                    assigned += 1

            available_reg = default_regset.copy()
            available_reg.remove('x0')
        count += 1
    if assigned != total_instr and len(available_reg) != 0:
        curr_swreg = available_reg[0]
        offset = 0
        for i in range(len(instr_dict)):
            if 'swreg' not in instr_dict[i]:
                instr_dict[i]['swreg'] = curr_swreg
                instr_dict[i]['offset'] = str(offset)
                offset += 4
    return instr_dict

def uformat_testreg(instr_dict):
    total_instr = len(instr_dict)
    available_reg = default_regset.copy()
    available_reg.remove('x0')
    count = 0
    assigned = 0
    for instr in instr_dict:
        if instr['rd'] in available_reg:
            available_reg.remove(instr['rd'])
        if instr['swreg'] in available_reg:
            available_reg.remove(instr['swreg'])

        if len(available_reg) <= 3:
            curr_testreg = available_reg[0]
            for i in range(assigned, count+1):
                if 'testreg' not in instr_dict[i]:
                    instr_dict[i]['testreg'] = curr_testreg
                    assigned += 1
            available_reg = default_regset.copy()
            available_reg.remove('x0')
        count += 1
    if assigned != total_instr and len(available_reg) != 0:
        curr_testreg = available_reg[0]
        for i in range(len(instr_dict)):
            if 'testreg' not in instr_dict[i]:
                instr_dict[i]['testreg'] = curr_testreg
    return instr_dict

def uformat_correct_val(instr_dict, op_node):
    for i in range(len(instr_dict)):
        imm_val = int(instr_dict[i]['imm_val'])
        correctval = eval(op_node['operation'])
        instr_dict[i]['correctval'] = str(correctval)
    return instr_dict



