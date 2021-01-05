import cv2
import numpy as np

def get_matches(img_left_gray, img_right_gray, num_keypoints=1000, threshold=0.8):
    '''Function to get matched keypoints from two images using ORB

    Args:
        img_left_gray (numpy array): of shape (H, W, C) with opencv representation of left image (i.e C: B,G,R)
        img_right_gray (numpy array): of shape (H, W, C) with opencv representation of right image (i.e C: B,G,R)
        num_keypoints (int): number of points to be matched (default=100)
        threshold (float): can be used to filter strong matches only. Lower the value stronger the requirements and hence fewer matches.
    Returns:
        match_points_a (numpy array): of shape (n, 2) representing x,y pixel coordinates of left image keypoints
        match_points_b (numpy array): of shape (n, 2) representing x,y pixel coordianted of matched keypoints in right image
    '''
    orb = cv2.ORB_create(nfeatures=num_keypoints)
    kp_l, desc_l = orb.detectAndCompute(img_left_gray, None)
    kp_r, desc_r = orb.detectAndCompute(img_right_gray, None)
    
    dis_matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches_list = dis_matcher.knnMatch(desc_l, desc_r, k=2) # get the two nearest matches for each keypoint in left image

    # for each keypoint feature in left image, compare the distance of the two matched keypoints in the right image
    # retain only if distance is less than a threshold 
    good_matches_list = []
    for match_1, match_2 in matches_list:
        if match_1.distance < threshold * match_2.distance:
            good_matches_list.append(match_1)
    
    #filter good matching keypoints 
    good_kp_l = []
    good_kp_r = []

    for match in good_matches_list:
        good_kp_l.append(kp_l[match.queryIdx].pt) # keypoint on the left image
        good_kp_r.append(kp_r[match.trainIdx].pt) # matching keypoint on the right image
    return np.array(good_kp_l), np.array(good_kp_r)

def normalize_pixels_coordinates(points_img_a, points_img_b):
    '''Function to normalize the pixel co-ordinates to have zero mean and unit standard deviation.

    Args:
        points_img_a (numpy array): of shape (n, 2) representing the points of Image A
        points_img_b (numpy array): of shape (n, 2) representing the matching points of Image B
    
    Returns:
        norm_points_img_a (numpy array): of shape (n, 2)
        norm_points_img_b (numpy array): of shape (n, 2)
        T_mat (numpy array): Transformation matrix that was used to normalize points
    '''
    num_points = points_img_a.shape[0]
    x_all_points = np.concatenate((points_img_a[:, 0], points_img_b[:, 0]), axis=0)
    y_all_points = np.concatenate((points_img_a[:, 1], points_img_b[:, 1]), axis=0) 
    mu_x =  np.mean(x_all_points)
    std_x = np.std(x_all_points)
    mu_y = np.mean(y_all_points)
    std_y = np.std(y_all_points)
    # normalization using x_n = (x - mu)/std
    # implemented as a matrix to take advantage of matrix multiplication to normalize
    epsilon = 1e7 # for numerical stability while division
    T_mat = np.array([[1 / (std_x + epsilon), 0, -mu_x / (std_x + epsilon)],
                      [0, 1 / (std_y + epsilon), -mu_y / (std_y + epsilon)],
                      [0, 0, 1]])
    
    # add a 3rd column of ones to the point numpy representation to make use of matrix multiplicate transform
    ones_col = np.ones((num_points,1))
    points_img_a = np.concatenate((points_img_a, ones_col), axis=1)
    points_img_b = np.concatenate((points_img_b, ones_col), axis=1)

    norm_points_img_a = (np.matmul(T_mat, points_img_a.T)).T[:,0:2]
    norm_points_img_b = (np.matmul(T_mat, points_img_b.T)).T[:,0:2]
    return norm_points_img_a, norm_points_img_b, T_mat