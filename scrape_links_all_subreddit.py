#Scrape Reddit to get links to all images posted in top level comments
#Photo battle subreddit requires users to post altered images as comments 

import urllib2
import praw, urllib, re, os, pickle, time, random #Reddit API for Python
from praw.helpers import submissions_between

NUM_IMGS_PER_COMMENT = 10**6 #basically as many as possible
NUM_LINKS_TO_GET = 50000
LINK_FILE_TRAIN = "links-topyear-all-train3.txt" #file to write (train) links to
LINK_FILE_TEST = "links-topyear-all-test3.txt" #file to write (test) links to

#Main scraper
def scrape():
  reddit_obj = praw.Reddit(user_agent = "Fake Images Scraper")
  psbattle = reddit_obj.get_subreddit("photoshopbattles") #subreddit of interest
  #submissions = psbattle.get_top_from_year(limit=None)#, params={"after" : "t3_4cd8qr"})
  submissions = submissions_between(reddit_obj, psbattle, highest_timestamp = 1416475603.0) #leave lowest_timestamp and highest_timestamp blank to get all submissions

  img_count = 0 
  count_submissions = 1 
  img_count_train = 0
  img_count_test = 0
  link_file_train = open(LINK_FILE_TRAIN, "w")
  link_file_test = open(LINK_FILE_TEST, "w")

  while img_count < NUM_LINKS_TO_GET: #TODO need this?

    for submission in submissions: #go through each submission
      try:
        if img_count > NUM_LINKS_TO_GET:
          break
        print "next submission: ", submission
        if not submission:
          print "Not a submission"
        else:
          print "submission id: ", submission.id
          print "submission timestamp: ", submission.created_utc
          #decide if images from this submission will be for training or test
          link_file = None
          testing = False #are we adding images to testing or training

          #add first images to test (avoid divide by 0)
          #then add to test if we have more than 5x number of training images as testing
          #NOTE: add all images from a submission to train or test
          #otherwise classifier might have very similar images in training dataset
          if img_count_test == 0 or img_count_train / img_count_test >= 5: 
            testing = True
            link_file = link_file_test
          else:
            link_file = link_file_train
          #get all comments for now (note: may cause dataset imbalance?
          #also takes longer because more API calls)
          submission.replace_more_comments(limit=None, threshold = 0) #limit=None for all comments
          comments = [comment for comment in submission.comments if \
          not isinstance(comment, praw.objects.MoreComments) and comment.is_root][:NUM_IMGS_PER_COMMENT] #look for at most 10 images a comment

          count_comments = 1
          for comment in comments: #each (root) comment (containing image)
            #if we've made it this far assume image is original
            links = find_links(comment.body) #get links (presumably of images)

            #this link is valid so download image at this link
            for link in links:
              if "](" in link: #correct mistake made by regex: sometimes get http://imgur.com...](http://imgur.com...)
                link = link[:link.index("]")] #get only up to and not including the ]
              link = link.replace(")","") #because sometimes Imgur links have trailing )
              link_file.write(link + " ")
              link_file.write(submission.id + " ")
              link_file.write(str(count_comments) + " ")
              link_file.write(str(img_count + 1) + "\n")
              img_count += 1
              if testing:
                img_count_test += 1
              else:
                img_count_train += 1

            count_comments += 1 #count comment
          count_submissions += 1 #count this submission as a new one
          print("%d valid comments on submission %d. Now %d image links total: %d train, %d test" \
            % (count_comments - 1, count_submissions - 1, img_count, img_count_train, img_count_test))
      except Exception as e:
        print "exception: ", e
    break

  #finish up
  link_file_train.close()
  link_file_test.close()
  print("%d image links scraped in total" % img_count)


#Input: text (e.g. reddit comment)
#Output: all valid hyperlinks
def find_links(text):
  #Source: http://stackoverflow.com/questions/6883049/regex-to-find-urls-in-string-in-python
  links = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
  return links

if __name__ == "__main__":
  scrape()
