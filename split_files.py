#Split up contents of directory into multiple folders of equal size

import os

def split_files(dir_name, num_batches):
	if not os.path.isdir(dir_name):
		raise ValueError("not a valid directory")
	files_list = os.listdir(dir_name)
	batch_size = len(files_list)/num_batches
	os.chdir(dir_name)
	for batch in range(num_batches):
		folder_name = "train3_" + str(batch + 1)
		os.system("mkdir " + folder_name)
		for file_num in range(batch_size * batch, batch_size*(batch+1)):
			os.system("mv " + files_list[file_num] + " " + folder_name)
		if batch == num_batches - 1: #move remaining images too
			for file_num in range(batch_size*(batch+1), len(files_list)):
				os.system("mv " + files_list[file_num] + " " + folder_name)
	print "Finished splitting files"
	print "Zipping files..."
	dirs_list = os.listdir(os.getcwd())
	for dir_name in dirs_list:
		os.system("zip -r " + dir_name + ".zip " + dir_name)

def test_split():
	os.system("mkdir test_split")
	for i in range(22):
		os.system("touch test_split/file" + str(i) + ".txt")
	split_files("test_split", 5)

if __name__ == "__main__":
	if os.path.isdir("test_split"):
		os.system("rm -rf test_split")
	#test_split()
	split_files("train_links_2ndbatch_2ndtry", 12)
