import cv2

def process_feature(feature_name, feature):
    if feature_name == 'fish_cast':
        feature.mat = resize_img(feature.mat, 1.20, 1.20)
    elif feature_name == 'fish_bite':
        feature.mat = resize_img(feature.mat, 1.20, 1.20)
    elif feature_name == 'fish_ease':
        feature.mat = resize_img(feature.mat, 1.20, 1.20)

def resize_img(cv_image, fx, fy):
    output_image = cv2.resize(cv_image, None, fx=fx, fy=fy, interpolation=cv2.INTER_LINEAR)
    return output_image