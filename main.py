import cv2
import urllib
import numpy as np
from tensorflow.keras.models import load_model

#### 1 - Preprocessing Image
def preProcess(img):
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # CONVERT IMAGE TO GRAY SCALE
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)  # ADD GAUSSIAN BLUR
    imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, 1, 1, 11, 2)  # APPLY ADAPTIVE THRESHOLD
    return imgThreshold
#### 3 - Reorder points for Warp Perspective
def reorder(myPoints):
    myPoints = myPoints.reshape((4, 2))
    myPointsNew = np.zeros((4, 1, 2), dtype=np.int32)
    add = myPoints.sum(1)
    myPointsNew[0] = myPoints[np.argmin(add)]
    myPointsNew[3] =myPoints[np.argmax(add)]
    diff = np.diff(myPoints, axis=1)
    myPointsNew[1] =myPoints[np.argmin(diff)]
    myPointsNew[2] = myPoints[np.argmax(diff)]
    return myPointsNew


#### 3 - FINDING THE BIGGEST COUNTOUR ASSUING THAT IS THE SUDUKO PUZZLE
def biggestContour(contours):
    biggest = np.array([])
    max_area = 0
    for i in contours:
        area = cv2.contourArea(i)
        if area > 50:
            peri = cv2.arcLength(i, True)
            approx = cv2.approxPolyDP(i, 0.02 * peri, True)
            if area > max_area and len(approx) == 4:
                biggest = approx
                max_area = area
    return biggest,max_area
#### 4 - TO SPLIT THE IMAGE INTO 81 DIFFRENT IMAGES
def splitBoxes(img):
    rows = np.vsplit(img,9)
    boxes=[]
    for r in rows:
        cols= np.hsplit(r,9)
        for box in cols:
            boxes.append(box)
    return boxes

#### 4 - GET PREDECTIONS ON ALL IMAGES
def getPredection(boxes,model):
    result = []
    for image in boxes:
        ## PREPARE IMAGE
        img = np.asarray(image)
        img = img[4:img.shape[0] - 4, 4:img.shape[1] -4]
        img = cv2.resize(img, (28, 28))
        img = img / 255
        img = img.reshape(1, 28, 28, 1)
        ## GET PREDICTION
        predictions = model.predict(img)
        classIndex = model.predict_classes(img)
        probabilityValue = np.amax(predictions)
        ## SAVE TO RESULT
        if probabilityValue > 0.8:
            result.append(classIndex[0])
        else:
            result.append(0)
    return result


#### 6 -  TO DISPLAY THE SOLUTION ON THE IMAGE
def displayNumbers(img,numbers,color = (0,255,0)):
    secW = int(img.shape[1]/9)
    secH = int(img.shape[0]/9)
    for x in range (0,9):
        for y in range (0,9):
            if numbers[(y*9)+x] != 0 :
                 cv2.putText(img, str(numbers[(y*9)+x]),
                               (x*secW+int(secW/2)-10, int((y+0.8)*secH)), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                            2, color, 2, cv2.LINE_AA)
    return img
#### 6 - DRAW GRID TO SEE THE WARP PRESPECTIVE EFFICENCY (OPTIONAL)
def drawGrid(img):
    secW = int(img.shape[1]/9)
    secH = int(img.shape[0]/9)
    for i in range (0,9):
        pt1 = (0,secH*i)
        pt2 = (img.shape[1],secH*i)
        pt3 = (secW * i, 0)
        pt4 = (secW*i,img.shape[0])
        cv2.line(img, pt1, pt2, (255, 255, 0),2)
        cv2.line(img, pt3, pt4, (255, 255, 0),2)
    return img


#### 6 - TO STACK ALL THE IMAGES IN ONE WINDOW
def stackImages(imgArray,scale):
    rows = len(imgArray)
    cols = len(imgArray[0])
    rowsAvailable = isinstance(imgArray[0], list)
    width = imgArray[0][0].shape[1]
    height = imgArray[0][0].shape[0]
    if rowsAvailable:
        for x in range ( 0, rows):
            for y in range(0, cols):
                imgArray[x][y] = cv2.resize(imgArray[x][y], (0, 0), None, scale, scale)
                if len(imgArray[x][y].shape) == 2: imgArray[x][y]= cv2.cvtColor( imgArray[x][y], cv2.COLOR_GRAY2BGR)
        imageBlank = np.zeros((height, width, 3), np.uint8)
        hor = [imageBlank]*rows
        hor_con = [imageBlank]*rows
        for x in range(0, rows):
            hor[x] = np.hstack(imgArray[x])
            hor_con[x] = np.concatenate(imgArray[x])
        ver = np.vstack(hor)
        ver_con = np.concatenate(hor)
    else:
        for x in range(0, rows):
            imgArray[x] = cv2.resize(imgArray[x], (0, 0), None, scale, scale)
            if len(imgArray[x].shape) == 2: imgArray[x] = cv2.cvtColor(imgArray[x], cv2.COLOR_GRAY2BGR)
        hor= np.hstack(imgArray)
        hor_con= np.concatenate(imgArray)
        ver = hor
    return ver
  
  

  
  
  
  
def solve(bo):
    find = find_empty(bo)
    if not find:
        return True
    else:
        row, col = find
    for i in range(1,10):
        if valid(bo, i, (row, col)):
            bo[row][col] = i
            if solve(bo):
                return True
            bo[row][col] = 0
    return False

def valid(bo, num, pos):
    # Check row
    for i in range(len(bo[0])):
        if bo[pos[0]][i] == num and pos[1] != i:
            return False
    # Check column
    for i in range(len(bo)):
        if bo[i][pos[1]] == num and pos[0] != i:
            return False
    # Check box
    box_x = pos[1] // 3
    box_y = pos[0] // 3
    for i in range(box_y*3, box_y*3 + 3):
        for j in range(box_x * 3, box_x*3 + 3):
            if bo[i][j] == num and (i,j) != pos:
                return False
    return True

def print_board(bo):
    for i in range(len(bo)):
        if i % 3 == 0 and i != 0:
            print("- - - - - - - - - - - - - ")
        for j in range(len(bo[0])):
            if j % 3 == 0 and j != 0:
                print(" | ", end="")
            if j == 8:
                print(bo[i][j])
            else:
                print(str(bo[i][j]) + " ", end="")

def find_empty(bo):
    for i in range(len(bo)):
        for j in range(len(bo[0])):
            if bo[i][j] == 0:
                return (i, j)  # row, col
    return None
  
  
  
  
  
  
  
def solve_my_sudoku(update,sudoku_image):
  print('Setting UP')
  update.message.reply_text("wait...")
  import os
  #disable all debugging logs
  os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

  def intializePredectionModel():
      model = load_model('/myModel.h5')
      return model

  ########################################################################
  pathImage = sudoku_image
  heightImg = 450
  widthImg = 450
  model = intializePredectionModel()  # LOAD THE CNN MODEL
  
  ########################################################################
  req = urllib.request.urlopen(pathImage)
  arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
  img = cv2.imdecode(arr, -1) # 'Load it as it is'

  img = cv2.resize(img, (widthImg, heightImg))  #A SQUARE IMAGE
  imgBlank = np.zeros((heightImg, widthImg, 3), np.uint8)  #BLANK IMAGE FOR TESTING DEBUGING
  imgThreshold = preProcess(img)

  #FIND ALL COUNTOURS
  imgContours = img.copy() # COPY for testing
  imgBigContour = img.copy() # COPY for testing
  contours, hierarchy = cv2.findContours(imgThreshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # FIND ALL CONTOURS
  cv2.drawContours(imgContours, contours, -1, (0, 255, 0), 3) # DRAW ALL DETECTED CONTOURS

  #Find biggest contour ->sudoku
  biggest, maxArea = biggestContour(contours)
  if biggest.size != 0:
      biggest = reorder(biggest)
      ##print(biggest)
      cv2.drawContours(imgBigContour, biggest, -1, (0, 0, 255), 25) #drawing biggest contour
      pts1 = np.float32(biggest) # PREPARE POINTS FOR WARP
      pts2 = np.float32([[0, 0],[widthImg, 0], [0, heightImg],[widthImg, heightImg]]) # PREPARE POINTS FOR WARP
      matrix = cv2.getPerspectiveTransform(pts1, pts2) # GER
      imgWarpColored = cv2.warpPerspective(img, matrix, (widthImg, heightImg))
      imgDetectedDigits = imgBlank.copy()
      imgWarpColored = cv2.cvtColor(imgWarpColored,cv2.COLOR_BGR2GRAY)

      #### 4. SPLIT THE IMAGE AND FIND EACH DIGIT AVAILABLE
      imgSolvedDigits = imgBlank.copy()
      boxes = splitBoxes(imgWarpColored)
      ##print(len(boxes))
      # cv2.imshow("Sample",boxes[65])
      numbers = getPredection(boxes, model)
      
      imgDetectedDigits = displayNumbers(imgDetectedDigits, numbers, color=(255, 0, 255))
      numbers = np.asarray(numbers)
      posArray = np.where(numbers > 0, 0, 1)
      
      #find soln 
      board = np.array_split(numbers,9) #splitting array into subarrays of size 9
      try:
          solve(board)
      except:
          pass
      ##print(board)
      flatList = []
      for sublist in board:
          for item in sublist:
              flatList.append(item)
      solvedNumbers =flatList*posArray
      imgSolvedDigits= displayNumbers(imgSolvedDigits,solvedNumbers)

      #Overlay Sol
      pts2 = np.float32(biggest) # PREPARE POINTS FOR WARP
      pts1 =  np.float32([[0, 0],[widthImg, 0], [0, heightImg],[widthImg, heightImg]]) # PREPARE POINTS FOR WARP
      matrix = cv2.getPerspectiveTransform(pts1, pts2)  # GER
      imgInvWarpColored = img.copy()
      imgInvWarpColored = cv2.warpPerspective(imgSolvedDigits, matrix, (widthImg, heightImg))
      inv_perspective = cv2.addWeighted(imgInvWarpColored, 1, img, 0.5, 1)
      imgDetectedDigits = drawGrid(imgDetectedDigits)
      imgSolvedDigits = drawGrid(imgSolvedDigits)
      ##########FOR ALL STAGES OF SUDOKU
      imageArray = ([img,imgThreshold,imgContours, imgBigContour],
                    [imgDetectedDigits, imgSolvedDigits,imgInvWarpColored,inv_perspective])
      stackedImage = stackImages(imageArray, 1)
      ret= im.fromarray(inv_perspective)
      return ret
  else:
      print("No Sudoku Found")
      return 0
    
    
    
  
  

  
  
from PIL import Image as im
from io import BytesIO



from datetime import datetime
import requests

def sample_responses(input_text):
    user_message = str(input_text).lower()

    if user_message in ("hello","hi","sup"):
        return "Hey there! waiting for you to upload your sudoku problem."
      
      
      
      
      
import constants as keys
from telegram.ext import *
import datetime
import requests
import json
import logging
import os

print("Bot Started...")

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)


#####    Time greeting    ######
currentTime = datetime.datetime.now()
currentTime.hour
if currentTime.hour < 12:
    greetings = 'Good morning, '
elif 12 <= currentTime.hour < 18:
    greetings = 'Good afternoon, '
else:
    greetings = 'Good evening, '
####################################################################

def start_command(update,context):
    rply = greetings+update.message.chat.first_name
    txt="\nThis bot helps you solving sudoku problems.\nJust upload the picture of the sudoku and we will provide you the solution."
    update.message.reply_text(rply+txt)

def help_command(update,context):
    update.message.reply_text('Contact developers for help.')

def handle_image(update,context):

    file_id = update.message.photo[-1].file_id
    link = "https://api.telegram.org/bot" + keys.API_KEY + "/getFile?file_id="+file_id
    response_API = requests.get(link)
    data = response_API.text
    parse_json = json.loads(data)
    d_link = "https://api.telegram.org/file/bot"+ keys.API_KEY +"/"+parse_json["result"]["file_path"]

    ret = solve_my_sudoku(update,d_link)
    if ret==0:
      update.message.reply_text("Please click clear image.")
      return;
    
    bio = BytesIO()
    bio.name = 'image.jpeg'
    ret.save(bio, 'JPEG')
    bio.seek(0)
    context.bot.send_photo(update.message.chat_id, photo=bio)
    r = requests.get(d_link)



def handle_message(update,context):
    print(update)
    print("\n")
    text = str(update.message.text).lower()
    response = sample_responses(text)
    update.message.reply_text(response)


def error(update,context):
    print(f"|||| Update {update} caused error |||{context.error}")
    print("\n")

def main():
    updater = Updater(keys.API_KEY, use_context=True)
    dp = updater.dispatcher

    ##  commands starts with '/'  
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("help", help_command))

    dp.add_handler(MessageHandler(Filters.text,handle_message))
    dp.add_handler(MessageHandler(Filters.photo,handle_image))
    dp.add_handler(MessageHandler(Filters.document,handle_image))
  
    dp.add_error_handler(error)
    '''
    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",port=PORT,url_path=keys.API_KEY)
    # updater.bot.set_webhook(url=settings.WEBHOOK_URL)
    updater.bot.set_webhook(APP_NAME + keys.API_KEY)
    '''
    updater.start_polling()
    updater.idle()
 
main()
