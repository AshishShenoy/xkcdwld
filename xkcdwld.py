import requests
import logging
import re
import os
import sys
from bs4 import BeautifulSoup
from tqdm import tqdm


def initLogging():
    logging.basicConfig(
        filename = "xkcdwld.log",
        level = logging.DEBUG,
        format = " %(asctime)s - %(levelname)s - %(message)s",
    )
    # logging.disable(logging.CRITICAL)
    logging.info("Start of execution")


def getInitialSoup():
    html = requests.get("https://www.xkcd.com", timeout = (3.05, 27))
    if not (200 <= html.status_code <= 300):
        logging.critical("Unexpected error during initial connection.")
        sys.exit("An unexpected error has occurred with the connection to the server.")
    return BeautifulSoup(html.text, features = "html.parser")


def getTotalComics(homepageSoup):
    countObject = homepageSoup.select_one("#middleContainer", parser = "html.parser")
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


# TODO: Add a progress bar.
# TODO: Add multithreaded downloads.
# TODO: Add GUI.
def downloadComics(numToDownload, total, soup):
    os.makedirs("XKCD Comics", exist_ok = True)
    logging.info(f"{numToDownload} comics to be downloaded.")

    for num in range(1, numToDownload + 1):
        comicNo = total - (num - 1)

        imageObject, downloadError = downloadComic(comicNo, soup)
        if not downloadError:
            saveImage(comicNo, imageObject)
        
        prevSoup, linkError = pointToPreviousSoup(comicNo, soup)
        if linkError:
            print(f"{num} images have been successfully downloaded.")
            logging.critical(f"Unexpected error occurred while downloading comic image {comicNo}")
            sys.exit("An unexpected error has occurred with the connection to the server.")
        soup = prevSoup


def downloadComic(comicNo, soup):
    error = False
    imageElem = soup.select_one("#comic img", parser = "html.parser")
    if imageElem == []:
        print(f"Could not find comic image {comicNo}.")
        logging.debug(f"Could not find comic image {comicNo}.")
        error = True 
    else:
        imageLink = imageElem.get("src")
    
    print(f"Downloading comic number {comicNo}...")
    try:
        imageObject = requests.get("https:" + imageLink, timeout = (3.05, 27))
    except Exception as e:
        print(f"There was an error downloading comic {comicNo}.")
        logging.debug(f"Error downloading comic {comicNo}: {e}")
        error = True

    return imageObject, error


def saveImage(comicNo, image):
    with open(os.path.join("XKCD Comics", "xkcd" + str(comicNo) + ".png"), "wb") as imageFile:
        for chunk in image.iter_content(1024 * 128):
            imageFile.write(chunk)


def pointToPreviousSoup(comicNo, soup):
    error = False
    prevTag = soup.select_one('a[rel="prev"]', parser = "html.parser")
    subLink = prevTag.get("href")
    prevImageLink = "https://www.xkcd.com" + subLink
    html = requests.get(prevImageLink, timeout = (3.05, 27))
    if not (200 <= html.status_code <= 300):
        error = True
        return None, error

    newSoup = BeautifulSoup(html.text, features = "html.parser")

    return newSoup, error


# TODO: Display a pop-up.
def displaySuccessMessage(num):
    print(f"{num} images have been successfully downloaded.")
    logging.info(f"{num} images have been successfully downloaded.")


def main():
    initLogging()

    xkcdSoup = getInitialSoup()
    totalComics = getTotalComics(xkcdSoup)

    # Allowing the option of downloading a specific number of latest comics through CL arguments.
    # Give no CL arguments to download all comics.
    if len(sys.argv) > 1:
        numToDownload = int(sys.argv[1]) if int(sys.argv[1]) <= totalComics else totalComics
    else:
        numToDownload = totalComics

    downloadComics(numToDownload, totalComics, xkcdSoup)
    displaySuccessMessage(numToDownload)


if __name__ == "__main__":
    main()