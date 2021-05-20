#normal 
import pickle 
import pandas as pd 
import os
import numpy as np 
import cv2
from tensorflow.keras.preprocessing import image
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from tensorflow.keras.utils import to_categorical
from PyFunctions import var
from skimage.segmentation import mark_boundaries 



def get_edged(img, dim): 
    '''This function will convert an image into an edged version using Gaussian filtering and return the edged photo''' 
    blurred = cv2.GaussianBlur(img, (3,3), 0)
    wide = cv2.Canny(blurred, 10,200)
    wide = cv2.resize(wide, dim, interpolation = cv2.INTER_CUBIC)
    return wide


def get_image_value(path, dim, edge = False): 
    '''This function will read an image and convert to a specified version and resize depending on which algorithm is being used.  If edge is specified as true, it will pass the img array to get_edged which returns a filtered version of the img'''
    if edge == True: 
        img = cv2.imread(path)
        edged = get_edged(img, dim)
        return edged
    else: 
        img = image.load_img(path, target_size = dim)
        img = image.img_to_array(img)
        return img/255

def get_img_array(img_paths, dim, edge, nn_type = 'normal'): 
    '''This fucntion takes a list of image paths and returns the np array corresponding to each image.  It also takes the dim and whether edge is specified in order to pass it to another function to apply these parameters.  This function uses get_image_value to perform these operations'''
    final_array = []
#     from tqdm import tqdm
#     for path in tqdm(img_paths):
    for path in img_paths:
        img = get_image_value(path, dim, edge)
        final_array.append(img)
    final_array = np.array(final_array)
    if edge:
        if nn_type != 'normal': 
            return np.stack((final_array,)*3, axis = -1)
        return final_array.reshape(final_array.shape[0], final_array.shape[1], final_array.shape[2], 1)
    else: 
        return final_array
        
def get_tts(nn_type, version = 1, edge = False, balance = False, pick = False):
    '''This function will creates a pickled file given the type of neural network architecture.  
    Using the Var.py file, the function will determine the specified dimension of the algorithm and create pickles given the NN type.  For this function to work, you must create a folder outside the repo called Pickles
    Version parameter corresponds to the type of train test split: 
        version = 1 --> using ROI and positives and hand dataset as negative
        version = 2 --> using positive and negative ROI
          
        edge --> corresponds to whether it should apply edge detection to the photos within the split'''
    if nn_type not in ['normal', 'mobilenet', 'vgg16']: 
        assert False
    
    if nn_type == 'normal': 
        DIM =  var.norm_dimension 
    elif nn_type == 'mobilenet': 
        DIM = var.mobilenet_dimension
    
    elif nn_type == 'inceptionnet': 
        DIM = var.inception_dimension
        
    elif nn_type == 'vgg16': 
        DIM = var.vgg_dimension
    elif nn_type == 'alexnet': 
        DIM = var.alex_dimension
    np.random.seed(10)
#Using Seperated ROI ang hand data 
    if version == 1:
        pistol_paths = [f'../Separated/FinalImages/Pistol/{i}' for i in os.listdir('../Separated/FinalImages/Pistol')] 
        pistol_labels = [1 for i in range(len(pistol_paths))]

        rifle_paths = [f'../Separated/FinalImages/Rifle/{i}' for i in os.listdir('../Separated/FinalImages/Rifle')] 
        rifle_labels = [2 for i in range(len(rifle_paths))]    

        neg_paths = [f'../hand_dataset/Neg/{i}' for i in os.listdir('../hand_dataset/Neg')]
        np.random.shuffle(neg_paths)
        neg_paths = neg_paths[:len(pistol_paths)- 500]
        neg_labels = [0 for i in range(len(neg_paths))]
        
    elif version == 2: 
        pistol_paths = [f'../Separated/FinalImages/Pistol/{i}' for i in os.listdir('../Separated/FinalImages/Pistol')] 
        pistol_labels = [1 for i in range(len(pistol_paths))]

        rifle_paths = [f'../Separated/FinalImages/Rifle/{i}' for i in os.listdir('../Separated/FinalImages/Rifle')] 
        rifle_labels = [2 for i in range(len(rifle_paths))]    

        neg_paths = [f'../Separated/FinalImages/NoWeapon/{i}' for i in os.listdir('../Separated/FinalImages/NoWeapon')]
        np.random.shuffle(neg_paths)
        neg_paths = neg_paths[:len(pistol_paths)- 500]
        neg_labels = [0 for i in range(len(neg_paths))]
        
        
    if balance == True: 
        np.random.shuffle(pistol_paths)
        pistol_paths = pistol_paths[:len(rifle_paths)+150]
        neg_paths = neg_paths[:len(rifle_paths)+150]
        
        pistol_labels = [1 for i in range(len(pistol_paths))]
        rifle_labels = [2 for i in range(len(rifle_paths))]
        neg_labels = [0 for i in range(len(neg_paths))]
    paths = pistol_paths + rifle_paths + neg_paths
    labels = pistol_labels + rifle_labels + neg_labels
    x_train, x_test, y_train, y_test = train_test_split(paths, labels, stratify = labels, train_size = .90, random_state = 10)

    if edge == True:      
        new_x_train = get_img_array(x_train, DIM, nn_type = nn_type, edge = True)
        new_x_test = get_img_array(x_test, DIM, nn_type = nn_type, edge = True)
    else: 
        new_x_train = get_img_array(x_train, DIM, edge = False)
        new_x_test = get_img_array(x_test, DIM, edge = False)
    
    print('Train Value Counts')
    print(pd.Series(y_train).value_counts())
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('Test Value Counts')
    print(pd.Series(y_test).value_counts())
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('X Train Shape')
    print(new_x_train.shape)
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('X Test Shape')
    print(new_x_test.shape)
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

    y_train = np.array(y_train)
    y_test = np.array(y_test)
    y_test = to_categorical(y_test)
    y_train = to_categorical(y_train)
    tts = (new_x_train, new_x_test, y_train, y_test)
    if pick == True:
        if edge == True:
            pickle.dump(tts, open(f'../Pickles/edge_{nn_type}_tts.p', 'wb'), protocol=4)
        else:
            pickle.dump(tts, open(f'../Pickles/{nn_type}_tts.p', 'wb'), protocol=4)
    
    return tts

        
        
def get_samples(nn_type, edge = False): 
    '''After performing the get_pickles function above, this function can be used to retrieve the pickled files given a specific NN type.  '''
    if edge == True: 
        x_train, x_test, y_train, y_test = pickle.load(open(f'../Pickles/edge_{nn_type}_tts.p', 'rb'))
    
    else: 
        x_train, x_test, y_train, y_test = pickle.load(open(f'../Pickles/{nn_type}_tts.p', 'rb'))

    return x_train, x_test, y_train, y_test

def non_max_suppression(boxes, overlapThresh= .5):
    '''This function performs non maxima suppression.  The function was taken from PyImageSearch.com.  Right now, there is still tweaking I must do to this function as it does only parts of what I intend it to''' 
    # if there are no boxes, return an empty list
    if len(boxes) == 0:
        return []
    # if the bounding boxes integers, convert them to floats --
    # this is important since we'll be doing a bunch of divisions
    if boxes.dtype.kind == "i":
        boxes = boxes.astype("float")
    # initialize the list of picked indexes	
    pick = []
    # grab the coordinates of the bounding boxes
    x1 = boxes[:,0]
    y1 = boxes[:,1]
    x2 = boxes[:,2]
    y2 = boxes[:,3]
    # compute the area of the bounding boxes and sort the bounding
    # boxes by the bottom-right y-coordinate of the bounding box
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(y2)
    # keep looping while some indexes still remain in the indexes
    # list
    while len(idxs) > 0:
        # grab the last index in the indexes list and add the
        # index value to the list of picked indexes
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)
        # find the largest (x, y) coordinates for the start of
        # the bounding box and the smallest (x, y) coordinates
        # for the end of the bounding box
        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])
        # compute the width and height of the bounding box
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)
        # compute the ratio of overlap
        overlap = (w * h) / area[idxs[:last]]
        # delete all indexes from the index list that have
        idxs = np.delete(idxs, np.concatenate(([last],
            np.where(overlap > overlapThresh)[0])))
    # return only the bounding boxes that were picked using the
    # integer data type
    return pick
    return boxes[pick].astype("int")
    

def get_img_prediction_bounding_box(path, model, dim, edge = False, model_type = 'normal'):
    '''This function will create a bounding box over what it believes is a weapon given the image path, dimensions, and model used to detect the weapon.  Dimensions can be found within the Var.py file.  This function is still being used as I need to apply non-max suppresion to create only one bounding box'''
    img = get_image_value(path, dim, edge = edge)

    if edge == True:
        img = img.reshape(1, img.shape[0], img.shape[1], 1)
    else: 
        img = img.reshape(1, img.shape[0], img.shape[1], 3)
    
    pred = model.predict(img)[0]
    
    category_dict = {0: 'No Weapon', 1: 'Handgun', 2: 'Rifle'}
    cat_index = np.argmax(pred)
    cat = category_dict[cat_index]
    print(f'{path}\t\tPrediction: {cat}\t{int(pred.max()*100)}% Confident')
    
    
    #speed up cv2
    cv2.setUseOptimized(True)
    cv2.setNumThreads(10)
    
    img = cv2.imread(path)

    clone = img.copy() 
    clone2 = img.copy()
    
#     if cat_index != 0:
    ss = cv2.ximgproc.segmentation.createSelectiveSearchSegmentation()
    ss.setBaseImage(img)
#     ss.switchToSelectiveSearchQuality()
    ss.switchToSelectiveSearchFast()

    rects = ss.process() 

    windows = []
    locations = []
    print(f'Creating Bounding Boxes for {path}')
    for x, y, w,h in rects[:1001]: 
        startx = x 
        starty = y 
        endx = x+w 
        endy = y+h 
        roi = img[starty:endy, startx:endx]
        if edge == True:
            roi = get_edged(roi, dim = dim)
        roi = cv2.resize(roi, dsize =dim, interpolation = cv2.INTER_CUBIC)
        windows.append(roi)
        locations.append((startx, starty, endx, endy))

    windows = np.array(windows)
    if edge == True:
        windows = windows.reshape(windows.shape[0], windows.shape[1], windows.shape[2], 1)
    else: 
        windows = windows.reshape(windows.shape[0], windows.shape[1], windows.shape[2], 3)
    windows = np.array(windows)
    locations = np.array(locations)
    
#     if model_type == 'mobilenet': 
#         from keras.applications.mobilenet import preprocess_input
#         windows = preprocess_input(windows)
    predictions = model.predict(windows)
    nms = non_max_suppression(locations)
    bounding_cnt = 0
    for idx in nms:
        if np.argmax(predictions[idx]) != cat_index: 
            continue
#         print(np.argmax(predictions[idx]), predictions[idx].max())
        startx, starty, endx, endy = locations[idx]
        cv2.rectangle(clone, (startx, starty), (endx, endy), (0,0,255), 2)
        text = f'{category_dict[np.argmax(predictions[idx])]}: {int(predictions[idx].max()*100)}%'
        cv2.putText(clone, text, (startx, starty+15), cv2.FONT_HERSHEY_SIMPLEX, .5, (0,255,0),2)
        bounding_cnt += 1

    if bounding_cnt == 0: 
        pred_idx= [idx for idx, i in enumerate(predictions) if np.argmax(i) == cat_index]
        cat_locations = np.array([locations[i] for i in pred_idx])
        nms = non_max_suppression(cat_locations)
        if len(nms)==0:
            cat_predictions = predictions[:,cat_index]
            pred_max_idx = np.argmax(cat_predictions)
            pred_max = cat_predictions[pred_max_idx]

            pred_max_window = locations[pred_max_idx]
            startx, starty, endx, endy = pred_max_window
            cv2.rectangle(clone, (startx, starty), (endx, endy),  (0,0,255),2)
            text = f'{category_dict[cat_index]}: {int(pred_max*100)}%'
            cv2.putText(clone, text, (startx, starty+15), cv2.FONT_HERSHEY_SIMPLEX, .5, (0,255,0),2)
        for idx in nms: 
            startx, starty, endx, endy = cat_locations[idx]
            cv2.rectangle(clone, (startx, starty), (endx, endy), (0,0,255), 2)
            text = f'{category_dict[np.argmax(predictions[pred_idx[idx]])]}: {int(predictions[pred_idx[idx]].max()*100)}%'
            cv2.putText(clone, text, (startx, starty+15), cv2.FONT_HERSHEY_SIMPLEX, .5, (0,255,0),2)
               


    
#     pick = func.non_max_suppression(locations, probs = None)

#     for idx in pick: 
#         startx, startx, endx, endy = locations[idx]
#         cv2.rectangle(clone, (startx, starty), (endx, endy), (0,0,255), 2)
        
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    cv2.imshow(f'Test', np.hstack([clone, clone2]))
    cv2.waitKey(0)
    ss.clear()


    return predictions



# def get_lime_predictions(base_folder, model, dim, save_name= None, iter = 3500): 
#     from lime import lime_image

#     '''This function will take a base folder containing images that will be run through the LIME package.  It will save the figure if a 
#     save_name is passed. '''
#     lime_images = [] 
#     original_images = []
#     for file in os.listdir(base_folder): 
#         print(f'Creating Lime Image for {file}')
#         path = f'{base_folder}/{file}'
#         img = get_image_value(path, dim)
#         original_images.append(img)
#         explainer = lime_image.LimeImageExplainer()
#         explanation = explainer.explain_instance(img, model.predict, top_labels = 5, hide_color = 0, num_samples = iter)
#         temp, mask = explanation.get_image_and_mask(explanation.top_labels[0], positive_only = False, num_features = 10, 
#                                                    hide_rest = False)
#         lime_img = mark_boundaries(temp/2 + .5, mask)
#         lime_images.append(lime_img)
#     lime_images = np.hstack(lime_images)
#     original_images = np.hstack(original_images)
#     joined_images = np.vstack([original_images, lime_images])
# #     cv2.imshow('Lime', joined_images)
# #     cv2.waitKey(0)
# #     cv2.destroyAllWindows()
#     plt.figure(figsize = (13,13))
#     plt.imshow(joined_images)
    
#     if save_name: 
#         plt.savefig(f'{save_name}')
# #         cv2.imwrite(save_name, joined_images)

# def get_vid_frames(path, model, dim, vid_name, edge = False): 
#     '''This function will take a path to an mp4 file.  After splitting the video into separate frames, it will run each frame through the model that is provided and create bounding boxes around each area the model believes is a weapon.  Once the bounding boxes are made, the function will combine each frame back into a video and save it to the path specified above. This function is used for creating bounding boxes within a video'''
#     from tqdm import tqdm
#     vid = cv2.VideoCapture(path)
#     total_frames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
#     pbar = tqdm(total = total_frames, desc = f'Splitting Video Into {total_frames} Frames')
#     images = [] 
#     sucess =1 
#     while True: 
#         try:
#             success, img = vid.read() 
#             img = cv2.resize(img, dim, interpolation = cv2.INTER_CUBIC)
#             images.append(img)
#             pbar.update(1)
#         except: 
#             break
        
#     pbar.close()
#     images = np.array(images)
    
#     clones = []
#     print(f'Creating {vid_name}.mp4')
#     for img in tqdm(images, desc = 'Getting Base Prediction and Extracting Sliding Window... Sit Back, This Will Take A While'): 
#         if edge == True:
#             img2 = img.reshape(1, img.shape[0], img.shape[1], 1)
#         else: 
#             img2 = img.reshape(1, img.shape[0], img.shape[1], 3)
#         clone = img.copy()

#         pred = model.predict(img2)[0]

#         category_dict = {0: 'No Weapon', 1: 'Handgun', 2: 'Rifle'}
#         cat_index = np.argmax(pred)
#         cat = category_dict[cat_index]
#         #if the prediction is non_weapon then continue to the next without creating a bounding box
#         if cat_index == 0: 
#             clones.append(clone)
#             continue
#         if cat in ['Handgun', 'Rifle']: 
#             cat = 'Weapon'
#         ss = cv2.ximgproc.segmentation.createSelectiveSearchSegmentation()
#         ss.setBaseImage(img)
#     #     ss.switchToSelectiveSearchQuality()
#         ss.switchToSelectiveSearchFast()

#         rects = ss.process() 

#         windows = []
#         locations = []
#         for x, y, w,h in rects[:1001]: 
#             startx = x 
#             starty = y 
#             endx = x+w 
#             endy = y+h 
#             roi = img[starty:endy, startx:endx]
#             if edge == True:
#                 roi = get_edged(roi, dim = dim)
#             roi = cv2.resize(roi, dsize =dim, interpolation = cv2.INTER_CUBIC)
#             windows.append(roi)
#             locations.append((startx, starty, endx, endy))

#         windows = np.array(windows)
#         if edge == True:
#             windows = windows.reshape(windows.shape[0], windows.shape[1], windows.shape[2], 1)
#         else: 
#             windows = windows.reshape(windows.shape[0], windows.shape[1], windows.shape[2], 3)
#         windows = np.array(windows)
#         locations = np.array(locations)

#         predictions = model.predict(windows)
#         nms = non_max_suppression(locations)
#         bounding_cnt = 0
#         for idx in nms:
#             if np.argmax(predictions[idx]) != cat_index: 
#                 continue
#             startx, starty, endx, endy = locations[idx]
#             cv2.rectangle(clone, (startx, starty), (endx, endy), (0,0,255), 2)
#             text = f'{cat}: {int(predictions[idx].max()*100)}%'
#             cv2.putText(clone, text, (startx, starty+15), cv2.FONT_HERSHEY_SIMPLEX, .5, (0,255,0),2)
#             bounding_cnt += 1

#         if bounding_cnt == 0: 
#             pred_idx= [idx for idx, i in enumerate(predictions) if np.argmax(i) == cat_index]
#             cat_locations = np.array([locations[i] for i in pred_idx])
#             nms = non_max_suppression(cat_locations)
#             if len(nms)==0:
#                 cat_predictions = predictions[:,cat_index]
#                 pred_max_idx = np.argmax(cat_predictions)
#                 pred_max = cat_predictions[pred_max_idx]

#                 pred_max_window = locations[pred_max_idx]
#                 startx, starty, endx, endy = pred_max_window
#                 cv2.rectangle(clone, (startx, starty), (endx, endy),  (0,0,255),2)
#                 text = f'{category_dict[cat_index]}: {int(pred_max*100)}%'
#                 cv2.putText(clone, text, (startx, starty+15), cv2.FONT_HERSHEY_SIMPLEX, .5, (0,255,0),2)
#             for idx in nms: 
#                 startx, starty, endx, endy = cat_locations[idx]
#                 cv2.rectangle(clone, (startx, starty), (endx, endy), (0,0,255), 2)
#                 text = f'{cat}: {int(predictions[pred_idx[idx]].max()*100)}%'
#                 cv2.putText(clone, text, (startx, starty+15), cv2.FONT_HERSHEY_SIMPLEX, .5, (0,255,0),2)
#         clones.append(clone)
        
    vid_dim = dim
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(f'Tests/VideoOutput/{vid_name}.mp4',fourcc, 10, vid_dim) #change the filename to whatever you would like

    out_writer = [out.write(i) for i in clones]
    out.release()
    cv2.destroyAllWindows()
    return clones