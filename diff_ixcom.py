from ixcom.grep import read_file
from ixcom.protocol import getMessageWithID, getParameterWithID, MessagePayloadDictionary
from numpy import interp, maximum, minimum, sign, deg2rad
from collections import defaultdict
from sys import stderr
from io import BytesIO
from copy import copy

def verbose(*text, **kwds):
    print(*text, file=stderr, **kwds)
    
def parse_args():
    import argparse
    class EvalAction(argparse.Action):       
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, eval(values))
        
    parser = argparse.ArgumentParser()
    parser.add_argument("first", help="First iXCOMstream.bin file to compare")
    parser.add_argument("second", help="Second iXCOMstream.bin file to compare")
    parser.add_argument("-o", "--output", help="output file", default=None)
    parser.add_argument("-l", "--logs", help="log to rewrite", default='POSTPROC,INSSOL')
    parser.add_argument("-f", "--fields", help="fields to rewrite", default=['acc','omg', 'vel', 'rpy', 'q_nb'],  action='append')
    parser.add_argument("-t", "--time", help="name of time field", default='gpstime')
    parser.add_argument("-p", "--percentage", help="percentage shown on progress", default=10, type=int)
    parser.add_argument("--min_time", help="minimum time stamp", default=1000, type=float)
    parser.add_argument("--max_time", help="maximum time stamp", default=float('Inf'), type=float)
    parser.add_argument("-a", "--axes", help="modified axes of second dataset (starting with 1)", default="1,2,3")
    parser.add_argument("-v", "--vel_axes", help="modified velocity axes of second dataset (starting with 1)", default="1,2,3")
    parser.add_argument("-r", "--rpy_axes", help="modified rpy axes of second dataset (starting with 1)", default="1,2,3")
    parser.add_argument("-i", "--imu_axes", help="modified postproc IMU axes of second dataset (starting with 1)", default="1,2,3")
    parser.add_argument("-q", "--quat_axes", help="modified postproc quaternion axes of second dataset (starting with 1)", default="1,2,3")
    parser.add_argument("-m", "--misalignment", help="migalignbment offset angle", default="0,0,0")
    #parser.add_argument("--func", help="function", default='substract', action=EvalAction)   
    
    return parser.parse_args()

args = parse_args()


    

#print(args.first, args.second)
msg_map = dict();
for elt in MessagePayloadDictionary:
    msg = MessagePayloadDictionary[elt]
    name = msg.get_name()
    msg_map[name] = elt

log_ids = [msg_map[log] for log in args.logs.replace("'","").split(',')]
    
axes_val = [int(idx) for idx in args.axes.replace("'","").split(',')]
axes = [abs(idx) - 1 for idx in axes_val]

angle_axes_val = [int(idx) for idx in args.rpy_axes.replace("'","").split(',')]
angle_axes = [abs(idx) - 1 for idx in angle_axes_val]

vel_axes_val = [int(idx) for idx in args.vel_axes.replace("'","").split(',')]
vel_axes = [abs(idx) - 1 for idx in vel_axes_val]

imu_axes_val = [int(idx) for idx in args.imu_axes.replace("'","").split(',')]
imu_axes = [abs(idx) - 1 for idx in imu_axes_val]

quat_axes_val = [int(idx) for idx in args.quat_axes.replace("'","").split(',')]
quat_axes = [abs(idx) for idx in quat_axes_val]

axes_map_ = defaultdict(lambda: axes)
axes_map_.update({'rpy': angle_axes })
ins_axes_map_ = copy(axes_map_)
ins_axes_map_ .update({'vel': vel_axes }) 

axes_map_ .update({'vel': [0,1,2] }) 
axes_map_ .update({'omg': imu_axes }) 
axes_map_ .update({'acc': imu_axes }) 
axes_map_ .update({'q_nb': quat_axes }) 

axes_map = {64: axes_map_, 3 : ins_axes_map_} 

factors = [sign(idx) for idx in axes_val ]

angle_factors = [sign(idx) for idx in angle_axes_val ]
vel_factors = [sign(idx) for idx in vel_axes_val ]
imu_factors = [sign(idx) for idx in imu_axes_val ]
quat_factors = [sign(idx) for idx in quat_axes_val ]

factors_map_ = defaultdict(lambda: factors)
factors_map_.update( {'rpy': angle_factors } )
ins_factors_map_ = copy(factors_map_)


ins_factors_map_ .update({'vel': vel_factors })
factors_map_.update({'vel': [1,1,1] })
factors_map_.update({'omg': imu_factors })
factors_map_.update({'acc': imu_factors })
factors_map_.update({'q_nb': quat_factors })

factors_map = {64: factors_map_, 3 : ins_factors_map_} 

misalignment = [ deg2rad(float(elt)) for elt in  args.misalignment.replace("'","").split(',') ]

verbose('Axes: ', axes_map, factors_map);

def diff_funcs(axes, factors, firsts, time1, seconds, time2):
    from numpy import hstack, subtract, interp
    indices = range(firsts.shape[1])
    res = list()
    for (idx , axis, fac) in zip(indices, axes, factors):
        interpolated = interp(time1, time2, seconds[:, axis])
        res.append( subtract(firsts[:,idx],  fac * interpolated) )
    return res

def diff_angles(axes, factors, firsts, time1, seconds, time2):
    from numpy import hstack, subtract, interp, unwrap
    indices = range(firsts.shape[1])
    res = list()
    for (idx , axis, fac) in zip(indices, axes, factors):
        interpolated = interp(time1, time2, unwrap(seconds[:,axis]) ) 
        res.append( subtract(unwrap(firsts[:,idx]),  (fac * interpolated)  - misalignment[axis] ) )
    return res


def diff_quat(axes, factors, firsts, time1, seconds, time2):
    from numpy import hstack, subtract, interp, unwrap
    indices = range(firsts.shape[1])
    res = list()
    allaxes  = [0] + axes
    allfacs  = [1] + factors
    interpols = [ interp(time1, time2, allfacs[elt]*seconds[:,allaxes[elt] ]) for elt in range(4)  ]
    
    res.append( firsts[:,0]*interpols[0]-firsts[:,1]*(-interpols[1])-firsts[:,2]*(-interpols[2])-firsts[:,3]*(-interpols[3]))
    res.append( firsts[:,1]*interpols[0]+firsts[:,0]*(-interpols[1])-firsts[:,3]*(-interpols[2])+firsts[:,2]*(-interpols[3]))
    res.append(firsts[:,2]*interpols[0]+firsts[:,3]*(-interpols[1])+firsts[:,0]*(-interpols[2])-firsts[:,1]*(-interpols[3]))
    res.append(firsts[:,3]*interpols[0]-firsts[:,2]*(-interpols[1])+firsts[:,1]*(-interpols[2])+firsts[:,0]*(-interpols[3]))

    return res


diff_func_map = {'acc': diff_funcs, 'omg': diff_funcs, 'vel': diff_funcs, 'rpy':  diff_angles, 'q_nb' : diff_quat}

    
def filter_file(filename):

    from os import SEEK_SET

    from ixcom.data import getMessageWithID
    from ixcom.grep import MessageSearcher, parse_message_from_buffer
    
    filtered_bytes_dict = dict()
    filtered_counter = dict()

    message_searcher = MessageSearcher(disable_crc = True)
    
    msg_bytes_queue = [BytesIO()]
    for id in log_ids:
        filtered_bytes_dict[id] = BytesIO()
        filtered_counter[id] = 0
        
    def callback(in_bytes):
        msg_id = int(in_bytes[1])
        
        if msg_id in log_ids:
            filtered_bytes_dict[msg_id].write(in_bytes)
            msg_bytes_queue.append((msg_id, filtered_counter[msg_id]))
            
            filtered_counter[msg_id] += 1
            
        else:
            if not isinstance(msg_bytes_queue[-1], BytesIO):
                msg_bytes_queue.append(BytesIO())
            msg_bytes_queue[-1].write(in_bytes)
       

    message_searcher.add_callback(callback)
    with open(filename, 'rb') as f:
        message_searcher.process_buffer_unsafe(f.read())

    result = dict()
         
    for msg_id in filtered_bytes_dict:
        filtered_bytes_dict[msg_id].seek(0, SEEK_SET)
        
        msg = getMessageWithID(msg_id)
        result[msg_id] = parse_message_from_buffer(msg_id, filtered_bytes_dict[msg_id])


    return (result, msg_bytes_queue)

    
verbose("Reading files...")
(first, queue) = filter_file(args.first)
(second,q2) = filter_file(args.second)

idx_by_time = defaultdict(list)

if args.output:
    output = open(args.output, "wb")
else:
    import os
    output =  open(os.devnull, "wb")


min_time = args.min_time
max_time = args.max_time
time_field = args.time

for log in log_ids:  

    data = first[log]
    reference = second[log]
    verbose("Evaluating %s..."%(log)) 

    for field in args.fields:
        try:
            data_field = data[field]
        except:
            data_field = None
            
          
        if data_field is not None:
            verbose(" %s..."%(field)) 

            times =  reference[time_field]
            if len( times) ==0:
                times = [-1000]
        
            min_time = maximum(min_time, maximum(min(data[time_field]), min(times)))
            max_time = minimum(max_time, minimum(max(data[time_field]), max(times)))
            func = diff_func_map[field]
            
            res = func(axes_map[log][field],factors_map[log][field], data_field, data[time_field], reference[field], reference[time_field])           
            for idx in range(data_field.shape[1]):
                verbose("Evaluating %s[%s][:,%d]..."%(log, field, idx)) 
                data[field][:,idx] = res[idx]


verbose("Time range: %f .. %f."%(min_time, max_time)) 
percent = round( args.percentage * len(queue) / 100)

verbose("Writing result file...")  
for (counter, chunk) in enumerate(queue):
    if ((counter % percent) == 0):
        verbose("%d%%" % (int(args.percentage * counter / percent)) )
        
    if isinstance(chunk, BytesIO):
        output.write(chunk.getvalue())
    else:
        (msg_id, counter) = chunk
        current = first[msg_id][counter]
        
        if (current[time_field] >= min_time) and (current[time_field] <= max_time):
            buffer = bytes(current)
            
            msg = getMessageWithID(msg_id)
            msg.from_bytes(buffer)
            
            output.write(msg.to_bytes())
        


