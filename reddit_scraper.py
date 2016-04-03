#Scrape Reddit to get links to all images posted in top level comments
#Photo battle subreddit requires users to post altered images as comments 

import urllib2
import praw, urllib, re, os, pickle, time #Reddit API for Python

#TODO: get submissions more than one at a time
#TODO: profile code. figure out why url request is so slow?

#Make HEAD requests without transferring entire file
class HeadRequest(urllib2.Request):
    def get_method(self):
        return 'HEAD'

#Main scraper
def scrape():
  VISITED_FNAME = "visited_submissions"
  NUM_SUBMISSION_AT_TIME = 3 #how many submission to process at a time
  visited_submissions = set() #IDs of submissions we've already visited
  #NOTE: (submission, comment) would be more efficient
  #But then each time we ran program we'd have to check every comment
  #Given that activity probably dies off quickly, the slight increase
  #in thoroughness is probably not worth the loss of efficiency

  if os.path.isfile(VISITED_FNAME):
    visited_submissions = pickle.load(open(VISITED_FNAME, "r"))
  
  reddit_obj = praw.Reddit(user_agent = "Fake Images Scraper")
 
  psbattle = reddit_obj.get_subreddit("photoshopbattles") #subreddit of interest

  #For now just count all submissions and comments whether or not we got an image from it
  #We need to track all submissions anyway to make sure we don't look through them 
  #if we've already visited them
  #So submission, comment numbers may not be consecutive but they should increase

  #Keep going through submissions until you find you haven't checked them
  #http://stackoverflow.com/questions/16263217/python-praw-wrapper-logic-problems
#**********************
  last_submission_fname = "last_submission_info.txt"
  last_submission_file = open(last_submission_fname, "r") #read in info about where we left off
  last_submission_info = last_submission_file.readlines()
  print "last submission info: ", last_submission_info
  img_count = int(last_submission_info[0][:-1]) #start from where we left off (note: strip off trailing "\n")
  count_submissions = len(visited_submissions) + 1 #start counting (from 1) wherever we left off
  original_num_submissions = len(visited_submissions) #so we can count how many new submissions
  last_submission_fullname = "none" #id of last (oldest) submission we check
  while len(visited_submissions) - original_num_submissions < NUM_SUBMISSION_AT_TIME:
    first = psbattle.get_top(limit=1, params={"after": last_submission_info[1]}) #psbattle.get_new(limit=5) #submissions in that subreddit
    submission = next(first, None) #process one submission at a time

    if not submission:
      print "not a submission"
      break
      #continue

    #step backward to most recent unvisited submission
    while submission.id in visited_submissions:
      print "already seen submission: " + submission.id
      submission = next(psbattle.get_new(limit=1, params={"after": submission.fullname}),None)
      if not submission: #out of submissions
        break
    print "submission: ", submission
    print "submission full name: ", submission.fullname

    if submission:
      print "submission id: ", submission.id
      visited_submissions.add(submission.id) #make note we will have visited this submission
      #get all comments for now (note: may cause dataset imbalance?
      #also takes longer because more API calls)
      submission.replace_more_comments(limit=10, threshold = 0) #limit=None for all comments
      comments = [comment for comment in submission.comments if comment.is_root][:10] #get at most 10 root comments

      count_comments = 1
      for comment in comments: #each (root) comment (containing image)
        try:
          #if we've made it this far assume image is original
          links = find_links(comment.body) #get links (presumably of images)

          #this link is valid so download image at this link
          for link in links:
            link = link.replace(")","") #because sometimes Imgur links have trailing )
            save_result = save_image(link, count_submissions, submission.id, count_comments, img_count + 1)
            if save_result: #we saved an image
              img_count += 1
          count_comments += 1 #count comment
        except Exception as e:
          print "Exception ", e, " caused by comment ", comment
      count_submissions += 1 #count this submission as a new one
      print("%d valid comments on submission %d. Now %d images total" \
        % (count_comments - 1, count_submissions - 1, img_count))
      last_submission_fullname = submission.fullname #save id of submission we just checked
  print("%d images scraped" % img_count)
  pickle.dump(visited_submissions, open(VISITED_FNAME,"w"))
  with open(last_submission_fname, "w") as last_submission_file:
    last_submission_file.write(str(img_count) + "\n") #save how many images we checked this time
    last_submission_file.write(last_submission_fullname) #write id of last submission checked so we can pick up from it


#Input: text (e.g. reddit comment)
#Output: all valid hyperlinks
def find_links(text):
  #Source: http://stackoverflow.com/questions/6883049/regex-to-find-urls-in-string-in-python
  links = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
  return links

#Input: image link, count number (for submission and comment and overall image), submission ID
#Action: save image in directory
#Output: whether or not the image was saved successfully
def save_image(link, submission_number, submission_id, comment_number, img_count):
  valid_image, maintype = check_image_link_validity(link)

  #last check: sometimes imgur links are to webpage not image
  if not valid_image and maintype == "text/html" and "imgur.com/" in link:
    print "original link: ", link
    if link.endswith(".gifv"): #sometimes these throw us off
      link = link[:-1] #remove trailing v
    else:
      link += ".jpg" #extension doesn't matter but this redirects to image page
    valid_image, maintype = check_image_link_validity(link) #redo check with new link


  if valid_image: #save the image
    extension = maintype.split("/")[-1] 
    if extension == "html":
      print "Link for html \"image\": ", link
      print "maintype: ", maintype
    urllib.urlretrieve(link, "reddit_images/img_sub" + str(submission_number) \
      + "-" + submission_id + "-comment" + str(comment_number) + "-" \
      + str(img_count) +  "." + extension)
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
  scrape()