
def read_config(cfg_path):
	with open(cfg_path, 'rb') as cfg_file:
		cfg = {}
		for line in cfg_file.read().decode("utf-8").split("\r\n"):
			if line.strip() and not line.startswith("#") and "=" in line:
				(key, val) = line.split("=")
				key = key.strip()
				val = val.strip()
				if val.startswith("["):
					val = val[2:-2]
					cfg[key] = [v.strip() for v in val.split("', '")]					
				else:
					cfg[key] = val
		return cfg

def write_config(cfg_path, cfg):
	stream = "\r\n".join( [key+"="+str(val) for key, val in cfg.items()] )
	with open(cfg_path, 'wb') as cfg_file:
		cfg_file.write(stream.encode("utf-8"))

if __name__ == '__main__':
	cfg = read_config("config.ini")
	print(cfg)