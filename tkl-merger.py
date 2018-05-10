# Proposal for animation merger
# 1) Collect all keyframes for a digsite, count the abundance
# 2) Reduce to original amount of keyframes with k-means clustering
# https://docs.scipy.org/doc/scipy/reference/cluster.vq.html
# 3) Retrieve nearest index in final reduced key table for each keyframe (vq of kmeans)
# 4) Optional: Re-time the 2D time-key curves to minimize the amount of error.

from scipy.cluster.vq import vq, kmeans
import os
import numpy as np
from struct import iter_unpack, unpack_from, pack


def save_tkl(dir_models, dir_out, tkl_ref, loc_lut, rot_lut):
	with open(os.path.join(dir_models, tkl_ref+".tkl"), 'rb') as f:
		tklstream = f.read()
	tkl_b00, tkl_b01, tkl_b02, tkl_b03, tkl_remaining_bytes, tkl_name, tkl_b04, tkl_b05, tkl_b06, tkl_b07, tkl_b08, tkl_b09, tkl_b10, tkl_b11, tkl_b12, tkl_b13, num_loc, num_rot, tkl_i00, tkl_i01, tkl_i02, tkl_i03, tkl_len_data	=  unpack_from("4B I 6s 10B 2I 5I", tklstream, 4)
	
	print("\nWriting",tkl_ref,"to",dir_out)
	tkl_locs = [pack("3f", *l) for l in loc_lut]
	tkl_quats = [pack("4f", *q) for q in rot_lut]
	
	tkl_locs.extend([tkl_locs[0] for x in range(num_loc-len(tkl_locs))])
	tkl_quats.extend([tkl_quats[0] for x in range(num_rot-len(tkl_quats))])
	
	#tkl_len_data = len(tkl_locs)*16 + len(tkl_quats)*12

	tkl_header = pack("4s 4B I 6s 10B 2I 5I", b"TPKL", tkl_b00, tkl_b01, tkl_b02, tkl_b03, tkl_remaining_bytes, tkl_ref.encode("utf-8"), tkl_b04, tkl_b05, tkl_b06, tkl_b07, tkl_b08, tkl_b09, tkl_b10, tkl_b11, tkl_b12, tkl_b13, len(tkl_locs), len(tkl_quats), tkl_i00, tkl_i01, tkl_i02, tkl_i03, tkl_len_data)
	
	if not os.path.exists(dir_out): os.makedirs(dir_out)
	with open(os.path.join(dir_out, tkl_ref+".tkl"), 'wb') as f:
		f.write(b"".join( (tkl_header, b"".join(tkl_locs), b"".join(tkl_quats) ) ))

def read_tkl(in_path):
	#read the tkl
	print("\nReading",in_path)
	with open(in_path, 'rb') as f:
		tklstream = f.read()
	tkl_b00, tkl_b01, tkl_b02, tkl_b03, tkl_remaining_bytes, tkl_name, tkl_b04, tkl_b05, tkl_b06, tkl_b07, tkl_b08, tkl_b09, tkl_b10, tkl_b11, tkl_b12, tkl_b13, num_loc, num_rot, tkl_i00, tkl_i01, tkl_i02, tkl_i03, tkl_i04	=  unpack_from("4B I 6s 10B 2I 5I", tklstream, 4)
	#tkl_i04 probably another size value, close to tkl_remaining_bytes
	pos = 56
	
	#load the LUT data into arrays
	loc_start = pos
	loc_end = pos+12*num_loc
	rot_start = loc_end
	rot_end = loc_end+16*num_rot
	loc_shape = (num_loc, 3)
	rot_shape = (num_rot, 4)
	return np.ndarray(loc_shape, 'f', tklstream[loc_start:loc_end]), np.ndarray(rot_shape, 'f', tklstream[rot_start:rot_end])

def get_used_keys(filepath):
	print("\nLoading",os.path.basename(filepath))
	with open(filepath, 'rb') as f:
		datastream = f.read()
	
	#header
	remaining_bytes, tkl_ref, magic_value1, magic_value2, lod_data_offset, salt, u1, u2	 = unpack_from("I 8s 2L 4I", datastream, 8)
	scene_block_bytes, num_nodes, u3, num_anims, u4 = unpack_from("I 4H", datastream, 60)
	aux_node_data, node_data, anim_pointer = unpack_from("3I", datastream, 60+56)
	
	#print(aux_node_data, node_data, anim_pointer)
	#decrypt the addresses
	aux_node_data += 60 - salt
	node_data += 60 - salt
	anim_pointer += 60 - salt
	if aux_node_data == 124:
		anim_pointer = node_data
		node_data = aux_node_data
	
	tkl_path = os.path.join(os.path.dirname(filepath), tkl_ref.split(b"\x00")[0].decode("utf-8")+".tkl")
	loc_indices = []
	rot_indices = []
	#anims
	pos = anim_pointer
	anim_offsets = unpack_from(str(num_anims)+"I", datastream, pos)
	#read all anims
	for anim_offset in anim_offsets:
		pos = anim_offset + 60 - salt
		#name_len =  unpack_from("B", datastream, pos)[0]
		#anim_name = unpack_from(str(name_len)+"s", datastream, pos+1)[0].rstrip(b"\x00").decode("utf-8")
		ub1, ub2, num_groups, duration =  unpack_from("3I f", datastream, pos+16)
		channel_offsets = unpack_from(str(num_nodes)+"I", datastream, pos+32)
		#read all bone channels
		for i, channel_offset in enumerate(channel_offsets):
			#bone_name = bone_names[i]
			channel_offset += 60 - salt
			pos = channel_offset
			channel_mode, num_frames =  unpack_from("2H", datastream, pos)
			pos += 4
			if channel_mode != 2:
				# 0 = fallback trans, quat key
				# 1 = trans + rot keys
				# 2 = skip
				# 3 = fallback quat, trans key
				for i in range(0,num_frames):
					key_time, loc_index, rot_index = unpack_from("f H H", datastream, pos)
					#save the required keys - fallback is not relevant
					if channel_mode in (0, 1):
						rot_indices.append(rot_index)
					if channel_mode in (3, 1):
						loc_indices.append(loc_index)
					pos+=8
	print("recorded loc_indices",len(loc_indices))
	print("recorded rot_indices", len(rot_indices))
	return tkl_path, loc_indices, rot_indices

def save_new_keys(in_path, out_path, tkl_ref_out, loc_inds_new=[], rot_inds_new=[]):
	print("Saving",os.path.basename(in_path))
	with open(in_path, 'rb') as f:
		datastream = f.read()
	
	#header
	remaining_bytes, tkl_ref, magic_value1, magic_value2, lod_data_offset, salt, u1, u2	 = unpack_from("I 8s 2L 4I", datastream, 8)
	scene_block_bytes, num_nodes, u3, num_anims, u4 = unpack_from("I 4H", datastream, 60)
	aux_node_data, node_data, anim_pointer = unpack_from("3I", datastream, 60+56)
	
	#print(aux_node_data, node_data, anim_pointer)
	#decrypt the addresses
	aux_node_data += 60 - salt
	node_data += 60 - salt
	anim_pointer += 60 - salt
	if aux_node_data == 124:
		anim_pointer = node_data
		node_data = aux_node_data
	
	anim_pointers_block = []
	channels_bytes = []
	
	i_rot = 0
	i_loc = 0
	
	#anims
	pos = anim_pointer
	anim_offsets = unpack_from(str(num_anims)+"I", datastream, pos)
	out_offset = anim_pointer + num_anims * 4
	#read all anims
	for anim_offset in anim_offsets:
		pos = anim_offset + 60 - salt
		anim_pointers_block.append(pack('I', out_offset - 60 + salt))
		out_offset += 32 + num_nodes * 4
		
		channel_pointer_bytes = []
		channel_bytes = []
		
		name_len =  unpack_from("B", datastream, pos)[0]
		anim_name = unpack_from(str(name_len)+"s", datastream, pos+1)[0].rstrip(b"\x00").decode("utf-8")
		ub1, ub2, num_groups, duration =  unpack_from("3I f", datastream, pos+16)
		channel_pointer_bytes.append(pack('B 15s 3I f', name_len, anim_name.encode("utf-8"), ub1, ub2, num_groups, duration) )
			
		channel_offsets = unpack_from(str(num_nodes)+"I", datastream, pos+32)
		#read all bone channels
		for i, channel_offset in enumerate(channel_offsets):
			channel_pointer_bytes.append(pack('I', out_offset - 60 + salt))
			pos = channel_offset + 60 - salt
			channel_mode, num_frames =  unpack_from("2H", datastream, pos)
			channel_bytes.append(pack('2H', channel_mode, num_frames ))
			pos += 4
			#if channel_mode != 2:
			# 0 = fallback trans, quat key
			# 1 = trans + rot keys
			# 2 = skip
			# 3 = fallback quat, trans key
			for y in range(0,num_frames):
				key_time, loc_index, rot_index = unpack_from("f2H", datastream, pos)
				pos+=8
				if channel_mode in (0, 1):
					rot_index = rot_inds_new[i_rot]
					i_rot+=1
				if channel_mode in (3, 1):
					loc_index = loc_inds_new[i_loc]
					i_loc+=1
				#set indices we did not require back to 0 (so we don't get crazy IDs)
				if channel_mode in (0, 2):
					loc_index = 0
				if channel_mode in (3, 2):
					rot_index = 0
				channel_bytes.append(pack('f2H', key_time, loc_index, rot_index ))
			out_offset += 4 + num_frames * 8
			 
		#channel pointer bytes seem fine, but the actual keyframe data seems to be out of place
		channels_bytes += channel_pointer_bytes + channel_bytes
		
	anim_bytes = b"".join(anim_pointers_block + channels_bytes)
	
	# print("should", lod_data_offset + 60-anim_pointer)
	# print("really", len(anim_bytes))
	#anim_bytes = datastream[anim_pointer : lod_data_offset + 60]
	with open(out_path, 'wb') as f:	
		len_bones_bytes = 176 *num_nodes
		len_lod_bytes = len(datastream)-(lod_data_offset + 60)
		remaining_bytes = 112 + len_bones_bytes + len(anim_bytes) + len_lod_bytes
		
		lod_offset = anim_pointer-60+len(anim_bytes)

		f.write( b"".join( (pack("8s I 8s 2L I", b"TMDL", remaining_bytes, tkl_ref_out.encode("utf-8"), magic_value1, magic_value2, lod_offset), datastream[32:anim_pointer], anim_bytes, datastream[lod_data_offset + 60:]) ) )
	
	
def work(dir_models, dir_out, dinos, boss_tkl):

	#map each dino species all of its TMDs
	dino_to_tmds = {}
	for dino in dinos:
		dino_to_tmds[dino] = []
	
	print("Dinos:")
	for file in os.listdir(dir_models):
		for dino in dinos:
			f_l = file.lower()
			if dino.lower() in f_l and f_l.endswith(".tmd"):
				dino_to_tmds[dino].append(file)
				print(dino, ">",file)
				break
	print("boss_tkl:",boss_tkl)

	tkl_to_luts = {}
	tmd_to_keys={}
	for dino, tmds in dino_to_tmds.items():
		#we only get the animation data for the first TMD of this species because the other versions are identical, anyway
		tmd = tmds[0]
		#for tmd in tmds:
		tmd_path = os.path.join(dir_models, tmd)
		tkl_path, loc_indices, rot_indices = get_used_keys(tmd_path)
		
		#store or retrieve the LUT from TKLs
		if tkl_path.lower() not in tkl_to_luts:
			loc_lut, rot_lut = read_tkl(tkl_path)
			if boss_tkl.lower() in tkl_path.lower():
				num_locs_out = len(loc_lut)
				num_rots_out = len(rot_lut)
			tkl_to_luts[tkl_path.lower()] = (loc_lut, rot_lut)
		else:
			loc_lut, rot_lut = tkl_to_luts[tkl_path.lower()]
			print("using",os.path.basename(tkl_path.lower()) )
		loc_keys = loc_lut[loc_indices]
		rot_keys = rot_lut[rot_indices]
		#does not reduce here
		tmd_to_keys[tmd_path] = (loc_keys, rot_keys)

	#concatenate all input keys into one array for locs and one for quats
	#then reduce them with np.unique
	locs_all = np.concatenate( [v[0] for v in tmd_to_keys.values()])
	rots_all = np.concatenate( [v[1] for v in tmd_to_keys.values()])
	print("Input locs:",len(locs_all))
	print("Output locs:",len(rots_all))
	locs_all = np.unique(locs_all, axis=0)
	rots_all = np.unique(rots_all, axis=0)
	print("Input locs unique:",len(locs_all))
	print("Output locs unique:",len(rots_all))


	#basically, num_locs_in is only 1/4th of num_locs_out if we only look at the first TMD for each dino
	#so the other 3 resolutions are direct copies of the anim data
	num_locs_in = len(locs_all)
	num_rots_in = len(rots_all)
	print("\nKey Stats:")
	print("Input locs:",num_locs_in)
	print("Output locs:",num_locs_out)
	print("Input rots:",num_rots_in)
	print("Output rots:",num_rots_out)
	#make sure we don't bloat it up, but should we ever have too many input keys, make sure we don't get too long output
	min_locs_out = min( num_locs_in, num_locs_out)
	min_rots_out = min( num_rots_in, num_rots_out)
	print("min locs:",min_locs_out)
	print("min rots:",min_rots_out)
	print("\nReducing keys...")
	#create the reduced LUTs
	final_locs_lut, distortion = kmeans( locs_all, min_locs_out, thresh=1e-04,iter=5, check_finite=False )
	final_rots_lut, distortion = kmeans( rots_all, min_rots_out, thresh=1e-04, iter=2, check_finite=False )
	
	save_tkl( dir_models, dir_out, boss_tkl, final_locs_lut, final_rots_lut)

	#now find closest matching keys for each of our TMDs
	#and finally replace all indices with the new indices
	for tmd_path, keyframes in tmd_to_keys.items():
		print("\nReassigning",os.path.basename(tmd_path))
		loc_keys, rot_keys = keyframes
		
		loc_indices_new, distance = vq( loc_keys, final_locs_lut)
		rot_indices_new, distance = vq( rot_keys, final_rots_lut)

		tmd_name = os.path.basename(tmd_path)
		save_new_keys(tmd_path, os.path.join(dir_out, tmd_name), boss_tkl, loc_indices_new, rot_indices_new )

		
#path in which all input models and tkl files are stored
dir_models = "C:/Program Files (x86)/Universal Interactive/Blue Tongue Software/Jurassic Park Operation Genesis/JPOG/Data/Models"
#path in which all ouput will be created
dir_out = "C:/Program Files (x86)/Universal Interactive/Blue Tongue Software/Jurassic Park Operation Genesis/JPOG/Data/test"

#the dinos you want to merge into one digsite
#TODO: maybe get this from FslHunt.ini?
# dinos = "steg", "cerato", "dryo"
# dinos = "anky_hi", "alberto_hi", "pachy_hi"
dinos = "anky_hi", "alberto_test", "pachy_hi"

#the name of the output TKL file (must be used by at least one of the dinos you want to merge; will determine how many keys you may use)
# boss_tkl = "Dma"
boss_tkl = "Dhbja"
work(dir_models, dir_out, dinos, boss_tkl)
