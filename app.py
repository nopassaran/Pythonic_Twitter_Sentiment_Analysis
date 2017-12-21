import tweepy
import twitter
import json
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener
from twitter import Twitter, OAuth, TwitterHTTPError, TwitterStream
import sys
import csv
import re
import math
import numpy
import tweet_features
from collections import OrderedDict


times = 0

#function which search for 2 or more repetitions of a character and replace with the character itself
def replaceTwoOrMore(s):
    pattern = re.compile(r"(.)\1{1,}", re.DOTALL)
    return pattern.sub(r"\1\1", s)



def featureSelectionByFrequency(words,threshold):
    wordcount={}
    cnt = 0
    for word in words:
        if word not in wordcount:
            wordcount[word] = 1
            cnt+=1
        else:
            wordcount[word] += 1
    x = 0
    #print "Old words:",cnt
    fv = []
    for w in sorted(wordcount, key=wordcount.get, reverse=True):
        if x < threshold:
           fv.append(w)
        x+=1
    return fv


######################Naive Bayes classifier####################################
# This functions takes as arguments test tweet and the list of training
# tweets and calculates the propability of tweet to belong to the certain class
# by calculating the propability of each one of it's words
################################################################################
def bayes(test,trainlist):
    p = 1
    total = len(trainlist)
    isThere = False
    update = []
    for testword in test:
        if testword in trainlist:
            isThere = True
            update.append(testword)
    if isThere:
        for testword in update:
            occ = trainlist.count(testword)
            if occ==0:
                occ=1
            p = p*(float(occ)/float(total))
    else:
        p = 0
    p = p * 0.5
    return p



########/###############################Preprocess##################################################
#This function cleans each word of the tweet by erasing all the unnecessary characters or rejecting
#the word if it is found into the stopwords dictionary
###################################################################################################
def cleaningTrain(word):
        x = word.upper()
        y = replaceTwoOrMore(x)
        y = y.strip('\'"?,.#')
        if  re.search(r"^[a-zA-Z][a-zA-Z0-9]*$", y) is None:
            y = ""
        return y


 #y = "".join([letter if ord(letter) < 128 else '?' for letter in x])

#Twitter connection variables
consumer_key = '1kCUZ1rCajy0Bbsn9XRE7IvBG'
consumer_secret = 'ipo7jWDX6y2CrrWk5wvs6qFrFKMWJygIN0H8syS1qvXwGpjxxZ'
access_token = '701681215796080640-0wkcj9zQWjZIQPx5AmEIu5svf5HEUJw'
access_secret = 'BtcVd2WCGGaU8F8jUJVTfwDDKFs3yJCkxtXHRNNiF0ppj'
oauth = OAuth(access_token, access_secret, consumer_key, consumer_secret)
api = tweepy.API(oauth)
twitter_stream = TwitterStream(auth=oauth)


#open stopwords dictionary and store into list all the words of it
stop = []
for line in open('stopwords.txt', 'r'):
    stopword = line.upper()
    stopword = stopword.strip("\n")
    stop.append(stopword)

print "Preprocessing Training Tweets ..."
limit = 100000 #training limit
crr = csv.reader(open("Training1106.csv","rb"))
trainp = []#list with positive tweets
trainn = []#list with negative tweets
goodp = 0#keeped words in positive tweets
goodn = 0#keeped words in negative tweets
cut = 0#cutted words
loop = 1#loop-tweeter counter
before  = 0
for row in crr:
    if not str(row[0]).startswith("RT"):
        loop+=1
        if loop>limit:
            break;
        if row[1]=="Positive":
            before+=1
            words = re.sub('((www\.[\s]+)|(https?://[^\s]+))','URL',row[0])
            words = words.split(" ")
            for word in words:
                    y = cleaningTrain(word)
                    if len(y)>0 and y not in stop and not y=="URL":
                        trainp.append(y)
                        goodp+=1
                    else:
                        cut+=1

        else:
            words = re.sub('((www\.[\s]+)|(https?://[^\s]+))','URL',row[0])
            words = words.split(" ")
            for word in words:
                y = cleaningTrain(word)
                if len(y)>0 and y not in stop and not y=="URL":
                    trainn.append(y)
                    goodn+=1
                else:
                    cut+=1

"""
print 100*cut/(goodn+goodp+cut),"%"
print goodn+goodp+cut
"""
xx = len(trainp)
yy = len(trainn)
final = trainp + trainn
print "Feature Selection..."
oldl = len(final)
#mostRepresentative = (xx+yy)/10
final = featureSelectionByFrequency(final,5000)
newl = len(final)

"""
print "More frequent words:"
x = 1
for item in final[1:50]:
    print x,":",item
    x+=1
print "New words:",newl
"""

testp = [] #list of positive tested tweets
testn = [] #list of negative tested tweets
cr = csv.reader(open("s2.csv","rb"))


print "Preprocessing  Test Tweets ..."
tweet_count = 5000
for row in cr:
    if not str(row[0]).startswith("RT"):
       if row[1]=="Negative":
            words = re.sub('((www\.[\s]+)|(https?://[^\s]+))','URL',row[0])
            words = words.split(" ")
            temp = []
            for word in words:
                    y = cleaningTrain(word)
                    if len(y)>0 and y not in stop and y in final and not y=="URL":
                        temp.append(y)
            if len(temp)>0:
                testn.append(temp)
            tweet_count-=1
       elif row[1]=="Positive":
            words = re.sub('((www\.[\s]+)|(https?://[^\s]+))','URL',row[0])
            words = words.split(" ")
            temp = []
            for word in words:
                    y = cleaningTrain(word)
                    if len(y)>0 and y not in stop and y in final and not y=="URL":
                        temp.append(y)
            if len(temp)>0:
                testp.append(temp)
            tweet_count-=1
       if tweet_count==0:
            break


tp = []
for item in trainp:
    if item in final:
        tp.append(item)

tn = []
for item in trainn:
    if item in final:
        tn.append(item)


pt = 0#properly classifed from positives
pf = 0#misclassified from positives
tweets = 1
print "Starting classification..."
for item in testp:
    if len(item)>0:
        tweets+=1
        bayes1 = bayes(item,tp)
        if bayes1 >0:
            bayes2 = bayes(item,tn)
            if bayes2 > 0:
                if bayes1>=bayes2:
                    pt+=1
                else:
                    pf+=1
nt = 0 #properly classifed from negatives
nf = 0 #misclassified from negatives
for item in testn:
    if len(item)>0:
        tweets+=1
        bayes1 = bayes(item,tp)
        if bayes1>0:
            bayes2 = bayes(item,tn)
            if bayes2 > 0:
                if bayes1<=bayes2:
                    nt+=1
                else:
                    #print item
                    nf+=1

accuracy = float(pt+nt)/float(pt+nt+nf+pf)
print "Training set tweets:",limit,"\nTest set size:",tweets-1,"\nAccuracy:",pt+nt,"/",(pt+nt+nf+pf),"(",accuracy,"%)"

