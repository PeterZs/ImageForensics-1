#############
#FOR TESTING SMALL CHANGES WHILE MAIN SCRAPER IS RUNNING
#############

#Scrape Reddit to get links to all images posted in top level comments
#Photo battle subreddit requires users to post altered images as comments 

import urllib2
import praw, urllib, re, os, pickle, time #Reddit API for Python

#Make HEAD requests without transferring entire file
class HeadRequest(urllib2.Request):
    def get_method(self):
        return 'HEAD'

#Main scraper
def scrape():
  VISITED_FNAME = "visited_submissions"
  NUM_SUBMISSION_AT_TIME = 100 #how many submission to process at a time
  visited_submissions = set() #IDs of submissions we've already visited
  #NOTE: (submission, comment) would be more efficient
  #But then each time we ran program we'd have to check every comment
  #Given that activity probably dies off quickly, the slight increase
  #in thoroughness is probably not worth the loss of efficiency

  if os.path.isfile(VISITED_FNAME):
    visited_comments = pickle.load(open(VISITED_FNAME, "r"))
  
  reddit_obj = praw.Reddit(user_agent = "Fake Images Scraper")

  psbattle = reddit_obj.get_subreddit("photoshopbattles") #subreddit of interest

  #TODO: logic may not be good
  #If you only get 10 submissions at a time and you've already looked at all 10,
  #nothing happens
  #Better: keep going through submissions until you find you haven't checked them
  #http://stackoverflow.com/questions/16263217/python-praw-wrapper-logic-problems
  img_count = 0
  count_submissions = len(visited_submissions) #start counting wherever we left off
  original_num_submissions = len(visited_submissions) #so we can count how many new submissions
  while len(visited_submissions) - original_num_submissions < NUM_SUBMISSION_AT_TIME:
    first = psbattle.get_top(limit=1) #psbattle.get_new(limit=5) #submissions in that subreddit
    submission = next(first, None) #process one submission at a time

    if not submission:
      continue

    #step backward to most recent unvisited submission
    while submission.id in visited_submissions:
      submission = next(psbattle.get_new(limit=1, params={"after": submission.fullname}),None)
      if not submission: #out of submissions
        break
    print "submission: ", submission

    if submission:
      print "submission id: ", submission.id
      visited_submissions.add(submission.id) #make note we will have visited this submission
      #get all comments for now (note: may cause dataset imbalance?
      #also takes longer because more API calls)
      submission.replace_more_comments(limit=None, threshold = 0)
      count_submissions += 1
      comments = submission.comments

      count_comments = 1
      for comment in comments: #TODO figure out how to access roots directly
        try:
          #if we've made it this far assume image is original
          if comment.is_root: #this is a top level content
            links = find_links(comment.body) #get links (presumably of images)

            #this link is valid so download image at this link
            for link in links:
              link = link.replace(")","") #because sometimes Imgur links have trailing )
              save_image(link, count_submissions, submission.id, count_comments)
              img_count += 1
          count_comments += 1 #count comment if we were able to process it successfully
        except Exception as e:
          print "Exception ", e, " caused by comment ", comment
      print("%d valid comments on submission %d. Now %d images total" \
        % (count_comments, count_submissions, img_count))
    time.sleep(2) #comply with reddit policy
  print("%d images scraped" % img_count)
  pickle.dump(visited_comments, open(VISITED_FNAME,"w"))


#Input: text (e.g. reddit comment)
#Output: all valid hyperlinks
def find_links(text):
  #Source: http://stackoverflow.com/questions/6883049/regex-to-find-urls-in-string-in-python
  links = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
  return links

#Input: image link, ID number (for submission and comment)
#Action: save image in directory
#Output: None
#NOTE: some people put in links to an Imgur webpage with an image (http://imgur.com...)
#Our system does not process these, as it identifies them as html not an image
#Only images with i.imgur.com/... .<image_format_tag> are processed correctly
#TODO possibly change this, try to get image from webpage?
def save_image(link, submission_number, submission_id, comment_number):
  valid_image, maintype = check_image_link_validity(link)

  #last check: sometimes imgur links are to webpage not image
  if not valid_image and maintype == "text/html" and "imgur.com/" in link:
    print type(link)
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
      + "-" + submission_id + "-comment" + str(comment_number) + "." + extension)

#Input: link
#Output: boolean True if link is for valid image, False otherwise
# and request type
def check_image_link_validity(link):
  print "link being checked: ", link
  valid_image = True
  try:
    response = urllib2.urlopen(HeadRequest(link))
    maintype = response.headers['Content-Type'].split(';')[0].lower()
    print "Resource type: ", maintype
    #not valid image type
    #if not maintype not in ('image/png', 'image/jpeg', 'image/gif'): #gifv is also seen
    if not maintype.startswith("image/"):
      #logging.debug('invalid type')
      valid_image = False
  except Exception as e:
    print "Exception ", e
    print "Link: ", link
  return valid_image, maintype


if __name__ == "__main__":
  scrape()