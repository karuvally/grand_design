from pathlib import Path
import cv2
import dlib
import numpy as np
from contextlib import contextmanager
from wide_resnet import WideResNet

def draw_label(image, point, label, font=cv2.FONT_HERSHEY_SIMPLEX,
               font_scale=0.8, thickness=1):
    size = cv2.getTextSize(label, font, font_scale, thickness)[0]
    x, y = point
    cv2.rectangle(image, (x, y - size[1]), (x + size[0], y), (255, 0, 0), cv2.FILLED)
    cv2.putText(image, label, point, font, font_scale, (255, 255, 255), thickness, lineType=cv2.LINE_AA)


@contextmanager
def video_capture(*args, **kwargs):
    cap = cv2.VideoCapture(*args, **kwargs)
    try:
        yield cap
    finally:
        cap.release()


def yield_images():
    # capture video
    with video_capture(0) as cap:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        while True:
            # get video frame
            ret, img = cap.read()

            if not ret:
                raise RuntimeError("Failed to capture image")

            yield img


def yield_images_from_dir(image_dir):
    image_dir = Path(image_dir)

    for image_path in image_dir.glob("*.*"):
        img = cv2.imread(str(image_path), 1)

        if img is not None:
            h, w, _ = img.shape
            r = 640 / max(w, h)
            yield cv2.resize(img, (int(w * r), int(h * r)))



#    args = get_args()
depth = 16
k = 8
weight_file = 'agegender.hdf5'
margin = 0.4
img = cv2.imread('office.jpg')


# for face detection
detector = dlib.get_frontal_face_detector()

# load model and weights
img_size = 64
model = WideResNet(img_size, depth=depth, k=k)()
model.load_weights(weight_file)


input_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img_h, img_w, _ = np.shape(input_img)

# detect faces using dlib detector
detected = detector(input_img, 1)
faces = np.empty((len(detected), img_size, img_size, 3))
label_list=[]

if len(detected) > 0:
    for i, d in enumerate(detected):
        x1, y1, x2, y2, w, h = d.left(), d.top(), d.right() + 1, d.bottom() + 1, d.width(), d.height()
        xw1 = max(int(x1 - margin * w), 0)
        yw1 = max(int(y1 - margin * h), 0)
        xw2 = min(int(x2 + margin * w), img_w - 1)
        yw2 = min(int(y2 + margin * h), img_h - 1)
        cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
        # cv2.rectangle(img, (xw1, yw1), (xw2, yw2), (255, 0, 0), 2)
        faces[i, :, :, :] = cv2.resize(img[yw1:yw2 + 1, xw1:xw2 + 1, :], (img_size, img_size))

    # predict ages and genders of the detected faces
    results = model.predict(faces)
    predicted_genders = results[0]
    ages = np.arange(0, 101).reshape(101, 1)
    predicted_ages = results[1].dot(ages).flatten()
    

    # draw results
    for i, d in enumerate(detected):
        label = "{}, {}".format(int(predicted_ages[i]),
                                "M" if predicted_genders[i][0] < 0.5 else "F")
        label_list.append(label)
#            draw_label(img, (d.left(), d.top()), label)

#        cv2.imwrite("result.jpg", img)
    #label=[label]
    print(label_list)




'''
Here comes the chatbot part of the code
'''
import random
from eywa.nlu import Classifier
from eywa.nlu import EntityExtractor

CONV_SAMPLES = {
    'age'       : [ "What is this person's age", "Give me the age", "Find out the age of Abhijith",
                    "How old is Abhijith" ],
    'gender'    : [ "What is this person's gender", "Give me the gender", "Find out the gender of Abhijith"],
    'greetings' : ['Hi', 'hello', 'How are you', 'hey there', 'hey','hola'],
}

CLF = Classifier()
for key in CONV_SAMPLES:
    CLF.fit(CONV_SAMPLES[key], key)


X_AGE = [ "What is this person's age", "Give me the age of this person", "Find out the age of Abhijith",
             "How old is Abhijith" ]
Y_AGE = [ {"person":"person"}, {"person":"person"},{"person":"Abhijith"},{"person":"Abhijith"}]

EX_AGE = EntityExtractor()
EX_AGE.fit(X_AGE,Y_AGE)


X_GREETING = ['Hii', 'helllo', 'Howdy', 'hey there', 'hey', 'Hi']
Y_GREETING = [{'greet': 'Hii'}, {'greet': 'helllo'}, {'greet': 'Howdy'},
              {'greet': 'hey'}, {'greet': 'hey'}, {'greet': 'Hi'}]

EX_GREETING = EntityExtractor()
EX_GREETING.fit(X_GREETING, Y_GREETING)

X_GENDER = [ "What is the gender of Abhijith", "Give me this person gender", "Find out the gender of Abhijith","Is the person, a male or female","gender of this person "]
Y_GENDER = [ {"person":"Abhijith"},{"person":"person"},{"person":"Abhijith"},{"person":"person"},{"person":"person"}]

EX_GENDER = EntityExtractor()
EX_GENDER.fit(X_GENDER,Y_GENDER)

_EXTRACTORS = {'age':EX_AGE,
               'gender':EX_GENDER,
               'greetings':EX_GREETING}

def get_response(u_query):
    '''
    Accepts user query and returns a response based on the class of query
    '''
    responses = {}
    rd_i = random.randint(0, 2)

    # Predict the class of the query.
    q_class = CLF.predict(u_query)

    # Run entity extractor of the predicted class on the query.
    q_entities = _EXTRACTORS[q_class].predict(u_query)
    if q_class == 'age':
        res="\n"
        for i in range(len(label_list)):
            res += 'The age of '+q_entities['person']+str(i)+ '  is '+label_list[i][:2]+'\n'
        responses['age']=res    

    if q_class == 'gender':
        res="\n"
        for i in range(len(label_list)):
            res += 'The gender of '+q_entities['person']+str(i)+ ' is '+label_list[i][4:]+'\n'
        responses['gender']=res
        #responses['gender'] = 'The gender of '+q_entities['person']+' is '+label[0][4:]

    if q_class == 'greetings':
        responses['greetings'] = ['Hey', 'Hi there',
                                  'Hello'][rd_i]+['\n        what would you like me to do ?', '',
                                                  '\n        what would you like me to do ?'][rd_i]

    return 'Agent : '+responses[q_class]

if __name__ == '__main__':
    # Greeting user on startup.
    print(get_response('Hi'))

    while True:
        UQUERY = input('you   : ')
        if UQUERY == 'bye':
            break
        RESPONSE = get_response(UQUERY)
        print(RESPONSE)               

    

