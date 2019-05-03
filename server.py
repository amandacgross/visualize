from flask import Flask, render_template, request
# from io import TextIOWrapper, StringIO
import requests, string, json
from collections import defaultdict

import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
nltk.download('wordnet')
from nltk.stem.wordnet import WordNetLemmatizer

app = Flask(__name__)

client_id = 'a0d31485dd77a1c2f33de683b101afde31cf27da24c255a9887d73e6e2092e39'

ps = PorterStemmer()
lem = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))


class TextToImages:
    def __init__(self, text):
        self.text = text
        self.top_keywords = []
        self.top_images = []


# isolates each word in the text, discards any common insignificant words (stopwords) and
# returns the ten most frequently appearing words
def parse_file(contents):
    keyword_counts = defaultdict(int)   # maps word to number of appearances in text

    words = contents.decode().split()   # generate list of words from text
    for word in words:
        # make lowercase, remove punctuation and control characters
        word = word.lower()
        word = word.translate(str.maketrans('', '', string.punctuation))
        word = word.translate(str.maketrans("\n\t\r", "   "))
        # create/update count only for valid keywords
        if word not in stop_words and word != '':
            # word = lem.lemmatize(word)
            if word in keyword_counts:
                keyword_counts[word] += 1
            else:
                keyword_counts[word] = 1

    top_keywords = sorted(keyword_counts, key=keyword_counts.get, reverse=True)[:10]  # sort keyword_counts by number
                                                                                      # of counts and take top ten
    return top_keywords


# makes API call to retrieve a set of images for each top keyword, then selects the ten most frequently
# appearing images
def get_images(top_keywords):
    image_results = dict()         # maps image id to object with image content
    image_counts = defaultdict()   # maps image id to number of appearances in API calls

    for kwd in top_keywords:
        req_url = 'https://api.unsplash.com/search/photos?client_id=' + client_id + '&page=1&query=' + kwd
        # if keyword2:
        #     req_url += '%20' + keyword2
        response = requests.get(req_url).content   # make request, get response json
        images = json.loads(response)['results']   # grab the images from the response json
        for image in images:
            image_id = image['id']                 # use Unsplash's id for image
            if image_id in image_results:
                image_counts[image_id] += 1
            else:
                image_counts[image_id] = 1
                image_results[image_id] = image
        top_ids = sorted(image_counts, key=image_counts.get, reverse=True)[:10]   # sort image_counts by number
                                                                                  # of counts and take top ten
        top_images = []
        for id in top_ids:
            top_images.append(image_results[id])   # grab image object associated with these top ten images
    return top_images


@app.route('/')
def hello():
    return render_template('splash.html', images=None)


# This route is used when a file has been uploaded by user. Retrieves file from DOM and performs processing
@app.route('/upload', methods=['POST'])
def upload_file():
    # print("Posted file: {}".format(request.files['file']))
    contents = request.files['file'].read()  # retrieve file from DOM

    new_texttoimages = TextToImages(contents)
    top_keywords = parse_file(contents)
    new_texttoimages.top_keywords = top_keywords
    top_images = get_images(top_keywords)
    new_texttoimages.top_images = top_images

    images = []
    for image in top_images:
        images.append(image['urls']['full'])   # send only the image URL to frontend
    print('images', images)
    return render_template('splash.html', images=images)


if __name__ == '__main__':
    app.run(port=5000, debug=True)