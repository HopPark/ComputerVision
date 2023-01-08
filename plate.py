import cv2
import numpy as np
import pytesseract
import imutils
from PIL import Image
import requests
from datetime import datetime

Rect = [0,0,0,0]
def detectContours(img):
    img = cv2.Canny(img, 30, 200) #Apply Canny Edge Detection
    contours=cv2.findContours(img.copy(),cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    return sorted(contours,key=cv2.contourArea, reverse = True)[:10]
def convertImage(img):
    b,g,r = cv2.split(img)
    img = cv2.merge((r,g,b))
    return Image.fromarray(img)
def applyFilters(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #Convert to gray scale
    return cv2.bilateralFilter(gray, 13, 30, 30)
def detectPlate(contours):
    screenCnt = np.empty( shape=(0, 0) )
    for c in contours:
        peri = cv2.arcLength(c, True) # approximate the contour
        approx = cv2.approxPolyDP(c, 0.015 * peri, True)
        if len(approx) == 4: # if our approximated contour has four points, then it's a rectangle which is probably the plate
            screenCnt = approx
            recx,recy,recw,rech = cv2.boundingRect(approx)
            Rect[0],Rect[1],Rect[2],Rect[3] = recx,recy,recw,rech
            break
    return screenCnt
def removeInvalidCharacters(str):
    rtr = ""
    for i in str: 
        if(i.isalnum()) : rtr += i
    return rtr

def cropPlate(screenCnt,gray,img):
    mask = np.zeros(gray.shape,np.uint8)
    new_image = cv2.drawContours(mask,[screenCnt],0,255,-1,)
    new_image = cv2.bitwise_and(img,img,mask=mask)
    (x, y) = np.where(mask == 255)
    (topx, topy) = (np.min(x), np.min(y))
    (bottomx, bottomy) = (np.max(x), np.max(y))
    #Binary thresholding may be useful
    return gray[topx:bottomx+1, topy:bottomy+1]
def applyOcr(img) : return pytesseract.image_to_string(img, config='--psm 11').replace("\n","")

numvals = '1234567890'

def filterResults(r):
	filtered = []
	for i in range(len(r)):
		if (r[i].upper() == r[i] and len(r[i]) > 6 and len(r[i]) < 9 and r[i][0] in numvals and r[i][1] in numvals and not r[i][2] in numvals):
			filtered.append(r[i])
	return filtered

def giveResult(r, cars):
	r0 = filterResults(r)
	if (len(r0) < 10):
		return False
	items = {}
	for i in r0:
		try:
			items[i]+=1
		except:
			items[i] = 1

	maxKey = 0
	for key in items:
		if (items[key] > maxKey):
			maxKey = items[key]
			itm = key

	if (key in cars):
		# API: ARABA CIKISI YAPILACAK
		now = datetime.now()
		res = requests.get('http://34.239.29.217/hoppark/api/pl_logs/exit_car.php?pl_id=1&car_plate='+key+'&exit_date='+str(now.year)+'-'+str(now.month)+'-'+str(now.day)+'%20'+str(now.hour)+':'+str(now.minute)+':'+str(now.second))
		cars.pop(cars.index(key))
		print("=============")
		print(key, 'cikis yapti')
		print(res.json())
		print("=============")
	else:
		# API: ARARBA GIRISI YAPILACAK
		now = datetime.now()
		res = requests.get('http://34.239.29.217/hoppark/api/pl_logs/enter_car.php?pl_id=1&car_plate='+key+'&enter_date='+str(now.year)+'-'+str(now.month)+'-'+str(now.day)+'%20'+str(now.hour)+':'+str(now.minute)+':'+str(now.second))
		cars.append(key)
		print("=============")
		print(key, 'giris yapti')
		print(res.json())
		print("=============")
	return True

cars = []
cap = cv2.VideoCapture(0)
results = []
while (True):
	ret, img = cap.read()
	cv2.imshow('Stream', img)
	gray = applyFilters(img)
	contours = detectContours(gray)
	screenCnt = detectPlate(contours)
	if(screenCnt.size > 0):
		plateImg = cropPlate(screenCnt,gray,img)
		scannedText = removeInvalidCharacters(applyOcr(plateImg))
		results.append(scannedText)
	# CONFIGURE: EGER COK HIZLI OKUDUGU ICIN PLAKAYI IKI KEZ YAZIYORSA TRESHOLDU YUKSELT
	if (len(results) > 50):
		if (giveResult(results, cars)):
			results = []
			print('Arabalar:')
			print(cars)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break
