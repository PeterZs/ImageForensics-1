#Given file of image links, get images from them
#Multithreading tutorial from http://www.codingninja.co.uk/building-a-concurrent-web-scraper-with-python/
import urllib2, urllib, pickle, os #TODO get rid of one of these url imports
from joblib import Parallel, delayed
import multiprocessing
from threading import Thread
from uuid import uuid4
from PIL import Image
import time

#Timeout
import signal

def signal_handler(signum, frame):
    raise Exception("Timed out!")


#Input: name of file of links to get images from
# name of directory to save images to
def get_images_from_links(links_file_name, img_dir_name):
  #read in set of links as list (for parallelizing)
  links = list(pickle.load(open(links_file_name, "r")))
  #print "last link: ", links[-1]
  #links = links[:50]
  num_cores = multiprocessing.cpu_count()
  print "number of cores: ", num_cores

  num_links_originally = len(links)
  print("%d links" % num_links_originally)
  #read links in parallel
  Parallel(n_jobs=num_cores)(delayed(save_image_from_link)(link, img_dir_name) for link in links)
  '''
  for link_index in range(len(links)):
    if link_index % 50 == 0:
      print "link index ", link_index
    link = links[link_index]
    save_image_from_link(link,img_directory)
    #Thread(target=save_image_from_link, args=(link,img_directory)).start()
  '''

  #remove any files that are not images
  print "saved images"

  files = list(os.listdir(img_dir_name))
  Parallel(n_jobs=num_cores)(delayed(remove_if_not_image)(img_dir_name, img_file) for img_file in files)
  '''
  for img_file in os.listdir(img_dir_name):
    try:
      image = Image.open(img_file)
    except IOError: #file not image, so remove it
      num_non_images += 1
      os.remove(img_dir_name + "/" + img_file)
  '''
  #print("removed %d non-image files" % num_non_images)
  print("%d images saved from %d links" % (len(os.listdir(img_dir_name)), num_links_originally))

#Input: image filename, directory where file is located
#Action: remove image file if it is not an image
def remove_if_not_image(img_dir_name, img_file):
  try:
    image = Image.open(img_dir_name + "/" + img_file)
  except IOError: #file not image, so remove it
    os.remove(img_dir_name + "/" + img_file)

#Make HEAD requests without transferring entire file
class HeadRequest(urllib2.Request):
    def get_method(self):
        return 'HEAD'

#Input: link to save image from
# directory to save image to
#Action: save image to that link if valid image at that link
def save_image_from_link(link, image_dir_name):
  valid_image = True#, maintype = check_image_link_validity(link)
  print "processing link ", link

  if link.endswith(".gifv"): #sometimes these throw us off
    link = link[:-1] #remove trailing v
  if link.startswith("http://imgur.com"):
    link += ".jpg"

  #last check: sometimes imgur links are to webpage not image
  '''
  if not valid_image and maintype == "text/html" and "imgur.com/" in link:
    print "original link: ", link
    if link.endswith(".gifv"): #sometimes these throw us off
      link = link[:-1] #remove trailing v
    else:
      link += ".jpg" #extension doesn't matter but this redirects to image page
    valid_image, maintype = check_image_link_validity(link) #redo check with new link
  '''


  if valid_image: #save the image
    try:
      extension = "jpg" #maintype.split("/")[-1] 
      if extension == "html":
        print "Link for html \"image\": ", link
        #print "maintype: ", maintype
        #give them any name (uuid)
      print "Retrieving link: ", link

      #time out after a given amount of time
      signal.signal(signal.SIGALRM, signal_handler)
      signal.alarm(100)   # 100 seconds limit
      try:
          urllib.urlretrieve(link, image_dir_name + "/" + str(uuid4()) + "." + extension)
      except Exception, msg:
          print "Exception (timeout?)"
      #urllib.urlretrieve(link, image_dir_name + "/" + str(uuid4()) + "." + extension)
      #time.sleep(0.5)
      print "Got link"
    except Exception as e:
      print "Exception ", e
      print "caused by link ", link
  print "Returning result ", valid_image
  return valid_image

#Input: link
#Output: boolean True if link is for valid image, False otherwise
# and request type
def check_image_link_validity(link):
  print "link being checked: ", link
  valid_image = True
  maintype = None
  try:
    response = urllib2.urlopen(HeadRequest(link))
    maintype = response.headers['Content-Type'].split(';')[0].lower()
    print "Resource type: ", maintype
    #not valid image type
    if not maintype.startswith("image/"):
      #logging.debug('invalid type')
      valid_image = False
  except Exception as e:
    print "Exception ", e
    print "Link: ", link
  return valid_image, maintype

if __name__ == "__main__":
  links_file_name = "train2_links2" #"test_links_second_batch"
  img_directory = "train_links_2ndbatch_2ndtry" #"test_images_second_batch"
  get_images_from_links(links_file_name, img_directory)
