import vcf
import numpy as np
import ipdb
from . import parameters as params

def remove_duplicates(svs):
    for idx,row in enumerate(svs):
        #reorder breakpoints based on position or chromosomes
        sv_id, bp1_chr, bp1_pos, bp1_dir, bp2_chr, bp2_pos, bp2_dir, sv_class = row
        if (bp1_chr!=bp2_chr and bp1_chr>bp2_chr) or (bp1_chr==bp2_chr and bp1_pos > bp2_pos):
            svs[idx] = (sv_id, bp2_chr,bp2_pos,bp2_dir,bp1_chr,bp1_pos,bp1_dir,sv_class)
    return np.unique(svs)

def load_input_vcf(svin,class_field):
    sv_dtype = [s for i,s in enumerate(params.sv_dtype) if i not in [2,5]]
    
    sv_vcf = vcf.Reader(filename=svin)
    sv_dict = OrderedDict()
    for sv in sv_vcf:
        
        if sv.FILTER is not None:
            if len(sv.FILTER)>0:
                continue
        
        sv_dict[sv.ID] = {'CHROM': sv.CHROM, 'POS': sv.POS, 'INFO': sv.INFO}

#    svs = OrderedDict()
#    sv_vcf = np.genfromtxt(svin,dtype=params.sv_vcf_dtype,delimiter='\t',comments="#")
#    keys = [key[0] for key in params.sv_vcf_dtype]
#    
#    for sv in sv_vcf:
#        sv_id = sv['ID']
#        svs[sv_id] = OrderedDict()
#        for key,sv_data in zip(keys,sv):
#            if key=='INFO' or key=='ID': continue
#            svs[sv_id][key] = sv_data
#         
#        info = map(methodcaller('split','='),sv['INFO'].split(';'))
#        svs[sv_id]['INFO'] = OrderedDict()
#        
#        for i in info:
#            if len(i)<2: continue
#            name = i[0]
#            data = i[1]
#            svs[sv_id]['INFO'][name] = data
    
    svs = np.empty(0,sv_dtype)
    procd = np.empty(0,dtype='S50')

    for sv_id in sv_dict:
        try:
            sv = sv_dict[sv_id]
            mate_id = sv['INFO']['MATEID']
            mate = sv_dict[mate_id]
            
            if (sv_id in procd) or (mate_id in procd): 
                continue
            
            bp1_chr = sv['CHROM']
            bp1_pos = sv['POS']
            bp2_chr = mate['CHROM']
            bp2_pos = mate['POS']
            sv_class = sv['INFO'][class_field] if class_field!='' else ''

            procd = np.append(procd,[sv_id,mate_id])
            new_sv = np.array([(bp1_chr,bp1_pos,bp2_chr,bp2_pos,sv_class)],dtype=sv_dtype)        
            svs = np.append(svs,new_sv)
        except KeyError:
            print("SV %s improperly paired or missing attributes"%sv_id)
            continue
    
    return svs

def load_input_socrates(svin,use_dir,min_mapq,filt_repeats):
    #sv_dtype =  [s for s in params.sv_dtype] if use_dir else [s for i,s in enumerate(params.sv_dtype) if i not in [2,5]]
    sv_dtype = params.sv_dtype
    
    #TODO: make parsing of socrates input more robust
    soc_in = np.genfromtxt(svin,delimiter='\t',names=True,dtype=None,invalid_raise=False)
    svs = np.empty(0,dtype=sv_dtype)
    filtered_out = 0

    sv_id = 0
    for row in soc_in:
        try: 
            bp1 = row[params.bp1_pos].split(':')
            bp2 = row[params.bp2_pos].split(':')
            bp1_chr, bp1_pos = bp1[0], int(bp1[1]) 
            bp2_chr, bp2_pos = bp2[0], int(bp2[1])
            #classification = row['classification']
            if 'normal' in row.dtype.names:
                # has germline info, filter out
                if row['normal']=='normal':
                    continue
            if row[params.avg_mapq1]<min_mapq or row[params.avg_mapq2]<min_mapq:
                filtered_out += 1
                continue
            if filt_repeats!=[]:
                if row[params.repeat1] in filt_repeats and row[params.repeat2] in filt_repeats:
                    filtered_out += 1
                    continue
            add_sv = np.empty(0)
            
            bp1_dir = row[params.bp1_dir] if use_dir else '?'
            bp2_dir = row[params.bp2_dir] if use_dir else '?'
            
            add_sv = np.array([(sv_id,bp1_chr,bp1_pos,bp1_dir,bp2_chr,bp2_pos,bp2_dir,'')],dtype=sv_dtype)
            svs = np.append(svs,add_sv)
            sv_id += 1
        except IndexError:
            raise Exception('Supplied Socrates file does not match column names specified in the parameters.py file')
    
    print('Filtered out %d Socrates SVs, keeping %d SVs' % (filtered_out,len(svs)))            
    return remove_duplicates(svs)

def load_input_simple(svin,use_dir,class_field):
    #sv_dtype =  [s for s in params.sv_dtype] if use_dir else [s for i,s in enumerate(params.sv_dtype) if i not in [2,5]]
    sv_dtype = params.sv_dtype

    sv_tmp = np.genfromtxt(svin,delimiter='\t',names=True,dtype=None,invalid_raise=False)
    svs = np.empty(0,dtype=sv_dtype)
    sv_id = 0
    for row in sv_tmp:
        bp1_chr = str(row['bp1_chr'])
        bp1_pos = int(row['bp1_pos'])
        bp2_chr = str(row['bp2_chr'])
        bp2_pos = int(row['bp2_pos'])
        sv_class = row[class_field] if class_field!='' else ''
        add_sv = np.empty(0)
        bp1_dir = str(row['bp1_dir']) if use_dir else '?'
        bp2_dir = str(row['bp2_dir']) if use_dir else '?'
        add_sv = np.array([(sv_id,bp1_chr,bp1_pos,bp1_dir,bp2_chr,bp2_pos,bp2_dir,sv_class)],dtype=sv_dtype)
        svs = np.append(svs,add_sv)
        sv_id += 1
    return remove_duplicates(svs)
