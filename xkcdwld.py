import requests
import logging
import re
import os
import sys
import threading
from bs4 import BeautifulSoup


MAX_DOWNLOADS_PER_THREAD = 10


def initLogging():
    logging.basicConfig(
        filename = "xkcdwld.log",
        filemode = 'w',
        level = logging.DEBUG,
        format = " %(asctime)s - %(levelname)s - %(message)s",
    )
    # logging.disable(logging.CRITICAL)


def getTotalComics():
    xkcdSoup = getInitialSoup()
    countObject = xkcdSoup.select_one("#middleContainer", parser = "html.parser")
    text = countObject.getText()
    for line in text.split("\n"):
        if line.startswith("Permanent link to this comic: "):
            countText = line
    logging.debug(f"Text to extract total number of comics made from: '{countText}'")
    numRegex = re.compile(r"https://xkcd\.com/(\d+)/")
    matchObject = numRegex.search(countText)
    total = int(matchObject.group(1))
    logging.debug(f"Number of comics = {total}")
    return total


def getInitialSoup():
    html = requests.get("https://www.xkcd.com", timeout = (3.05, 27))
    if not (200 <= html.status_code <= 300):
        logging.critical("Unexpected error during initial connection.")
        sys.exit("An unexpected error has occurred with the initial connection to the server.")
    return BeautifulSoup(html.text, features = "html.parser")


def displayUsagePrompt(totalComics):
    print("This script can be used to download XKCD comics in multiple ways:")
    print()
    print("1. Download a certain number of recent comics, e.g. the 10 most recent comics.")
    print("2. Download comics within a certain comic number range, e.g. all comics between 1500 and 2000.")
    print("3. Download a specific list of comics, e.g. download comic number 877,1278 etc.")
    print()
    print(f"There have been {totalComics} XKCD comics made till date.")
    print()

    choice = int(input("Please enter your choice (1, 2 or 3): "))
    while choice not in [1,2,3]:
        choice = int(input("Please enter a valid choice: "))
    logging.info(f"User has chosen option {choice}.")
    return choice


# TODO: Add GUI.
def downloadComics(choice, totalComics):
    os.makedirs("XKCD Comics", exist_ok = True)

    if choice == 1:
        latestNum = int(input(f"Enter the number of recent comics to download (Maximum of {totalComics}): "))
        downloadLatest(latestNum, totalComics)

    elif choice == 2:
        lowerLimit = int(input(f"Enter the lower limit of the range (Between 1 and {totalComics}): "))
        upperLimit = int(input(f"Enter the upper limit of the range (Between {totalComics} and {lowerLimit}): "))
        downloadRange(lowerLimit, upperLimit)

    elif choice == 3:
        print(f"Enter a space seperated list of comic numbers to download (Maximum of {totalComics}): ", end = '')
        listOfComics = input().split()
        listOfComics = [int(comicNum) for comicNum in listOfComics]
        downloadSpecific(listOfComics)


def downloadLatest(num, total):
    downloadThreads = []
    numOfThreads = num // MAX_DOWNLOADS_PER_THREAD
    leftoverDownloads = num % MAX_DOWNLOADS_PER_THREAD

    comicNum = total - num + 1
    for _ in range(numOfThreads):
        downloadThread = threading.Thread(target = downloadLatestRange, 
                                          args = (comicNum, comicNum + MAX_DOWNLOADS_PER_THREAD))
        downloadThreads.append(downloadThread)
        downloadThread.start()
        comicNum += MAX_DOWNLOADS_PER_THREAD
    
    for _ in range(leftoverDownloads):
        downloadThread = threading.Thread(target = downloadLatestRange, 
                                          args = (comicNum, comicNum + 1))
        downloadThreads.append(downloadThread)
        downloadThread.start()
        comicNum += 1
    
    for downloadThread in downloadThreads:
        downloadThread.join()
    logging.info("All threads successfully executed.")


def downloadLatestRange(startComic, endComic):
    for comicNo in range(startComic, endComic):
        html = requests.get(f'http://xkcd.com/{comicNo}', timeout = (3.05, 27))
        if not (200 <= html.status_code <= 300):
            logging.error(f"HTTP GET Request to http://xkcd.com/{comicNo} failed.")
        soup = BeautifulSoup(html.text, features = "html.parser")

        comicElem = soup.select_one('#comic img')
        if comicElem == None:
            logging.error(f"The comic {comicNo} could not be downloaded.")
        else:
            comicUrl = "https:" + comicElem.get('src')
            logging.debug(f"Downloading image {comicUrl}.")

            try:
                imageObject = requests.get(comicUrl, timeout = (3.05, 27))
            except Exception as e:
                logging.error(e)

            if not (200 <= html.status_code <= 300):
                logging.error(f"HTTP GET Request to {comicUrl} failed.")
            else:
                saveImage(comicNo, imageObject)


def downloadRange(startComic, endComic):
    downloadThreads = []
    numOfThreads = (endComic - startComic) // MAX_DOWNLOADS_PER_THREAD
    leftoverDownloads = (endComic - startComic) % MAX_DOWNLOADS_PER_THREAD

    comicNum = startComic + 1
    for _ in range(numOfThreads):
        downloadThread = threading.Thread(target = downloadLatestRange, 
                                          args = (comicNum, comicNum + MAX_DOWNLOADS_PER_THREAD))
        downloadThreads.append(downloadThread)
        downloadThread.start()
        comicNum += MAX_DOWNLOADS_PER_THREAD
    
    for _ in range(leftoverDownloads):
        downloadThread = threading.Thread(target = downloadLatestRange, 
                                          args = (comicNum, comicNum + 1))
        downloadThreads.append(downloadThread)
        downloadThread.start()
        comicNum += 1
    
    for downloadThread in downloadThreads:
        downloadThread.join()
    logging.info("All threads successfully executed.")


def downloadSpecific(comicNumList):
    downloadThreads = []
    numOfThreads = len(comicNumList) // MAX_DOWNLOADS_PER_THREAD
    leftoverDownloads = len(comicNumList) % MAX_DOWNLOADS_PER_THREAD

    comicNumIndex = 0
    for _ in range(numOfThreads):
        downloadThread = threading.Thread(target = downloadLatestRange, 
                                          args = (comicNumList[comicNumIndex], 
                                                  comicNumList[comicNumIndex] + MAX_DOWNLOADS_PER_THREAD))
        downloadThreads.append(downloadThread)
        downloadThread.start()
        comicNumIndex += 1
    
    for _ in range(leftoverDownloads):
        downloadThread = threading.Thread(target = downloadLatestRange, 
                                          args = (comicNumList[comicNumIndex],
                                                  comicNumList[comicNumIndex] + 1 ))
        downloadThreads.append(downloadThread)
        downloadThread.start()
        comicNumIndex += 1    

    for downloadThread in downloadThreads:
        downloadThread.join()
    logging.info("All threads successfully executed.")


def saveImage(comicNo, image):
    with open(os.path.join("XKCD Comics", "xkcd" + str(comicNo) + ".png"), "wb") as imageFile:
        for chunk in image.iter_content(1024 * 128):
            imageFile.write(chunk)


# TODO: Display the number of comics successfully downloaded.
# TODO: Display a pop-up.
def displaySuccessMessage():
    print("The comics have been successfully downloaded.")
    logging.info("End of execution.")


def main():
    initLogging()
    
    totalComics = getTotalComics()
    userChoice = displayUsagePrompt(totalComics)
    downloadComics(userChoice, totalComics)

    displaySuccessMessage()


if __name__ == "__main__":
    main()