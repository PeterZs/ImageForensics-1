#Combine training or test links from multiple scraping batches
#Also allows us to check that there is no overlap between train and test data
#  and correct if there is

import os, pickle

#Input: name of a file of all links we want to create or add to
# name of file containing links to add
#Action: add link info to file of all links 
# (goal: avoid duplicate links, get just link itself and not
#other info that the scraper collects just in case)
def combine_links(links_file_name, links_to_add_file_name):
  links = set()

  #if we already have a list of all links so far
  if os.path.exists(links_file_name):
    #start by reading them in
    links = pickle.load(open(links_file_name,"r"))

  print("before reading in new links: %d links total" % len(links))

  #add links from our file
  links = read_in_links(links, links_to_add_file_name)

  print("after reading in new links: %d links total" % len(links))

  #save links
  pickle.dump(links, open(links_file_name, "w"))

#Input: a set of links and a name of file of links to add in
#Output: set of links with links in file added
def read_in_links(links, links_file_name):
  links_file = open(links_file_name, "r")
  links_info = links_file.readlines()
  for link in links_info:
    link_info = link.split() #info separated by split
    links.add(link_info[0]) #first part is actual link
  return links

#Input: train and test link files
#Output: boolean determining whether there is any overlap
def check_dataset_integrity(train_file_name, test_file_name):
  train_links = pickle.load(open(train_file_name, "r"))
  test_links = pickle.load(open(test_file_name, "r"))
  print("%d train, %d test links" % (len(train_links), len(test_links)))
  intersection = set.intersection(train_links, test_links)
  if len(intersection) > 0:
    #hopefully this won't happen but if it does we need to 
    #discard duplicate links from at least one dataset
    print("%d links in both datasets" % len(intersection))
    #train_links_no_duplicates = train_links - intersection
    #pickle.dump(train_links_no_duplicates, open("train_second_batch_no_duplicates","w"))
    #Remove duplicate links from test data
    #print("Removing duplicates from test data...")
    #test_links_no_duplicates = test_links - intersection
    #pickle.dump(test_links_no_duplicates, open(test_file_name, "w"))
    #print("Pruned test data links saved")
    #print("New dataset sizes: ")
    #print("Train data: %d" % len(train_links))
    #print("Test data: %d" % len(test_links_no_duplicates))
    return False 
  else:
    return True

#Get all links that aren't in a set of old links we already got images from
def get_new_links(all_links_set_fname, old_links_set_fname, new_links_set_fname):
	all_links = pickle.load(open(all_links_set_fname, "r"))
	old_links = pickle.load(open(old_links_set_fname, "r"))
	new_links = all_links - old_links
	print("%d new links" % len(new_links))
	pickle.dump(new_links, open(new_links_set_fname, "w"))
	
if __name__ == "__main__":
  #which mode to run program in
  read_data = False
  check_data = True
  separate_links = False

  if read_data: #we want to read data
    links_file_name = "train_links" #"train_links"
    links_to_add_file_name = "train_second_batch_no_duplicates" #"links-topyear-all-train3.txt"
    combine_links(links_file_name, links_to_add_file_name)
  if check_data: #we want to check integrity of our datasets
    train_links_file_name = "all_train_links_413"
    test_links_file_name = "all_test_links_413"
    print check_dataset_integrity(train_links_file_name, test_links_file_name)
  if separate_links:
    all_links_set_fname = "test_links"
    old_links_set_fname = "test_links_first_batch"
    new_links_set_fname = "test_links_second_batch"
    get_new_links(all_links_set_fname, old_links_set_fname, new_links_set_fname)

