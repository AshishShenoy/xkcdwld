import requests, bs4, re, sys, os
import logging


# Logging control.
logging.basicConfig(
    filename = "xkcdwld.log",
    level = logging.DEBUG,
    format = " %(asctime)s - %(levelname)s - %(message)s",
)
logging.disable(logging.CRITICAL)
logging.info("Start of execution")


# Open the xkcd page and create a response object.
html = requests.get("http://www.xkcd.com", timeout = (3.05, 27))
if html.status_code != 200:
    sys.exit("An unexpected error has occurred with the connection to the server.")
xkcdSoup = bs4.BeautifulSoup(html.text, features = "html.parser")


# Counting the number of xkcd comics made till date.
countObject = xkcdSoup.select("#middleContainer", parser = "html.parser")
text = countObject[0].getText()
countText = [
    line
    for line in text.split("\n")
    if line.startswith("Permanent link to this comic: ")
][0]
logging.debug(f"Text to extract NUMBER_OF_COMICS from: '{countText}'")
numRegex = re.compile(r"https://xkcd\.com/(\d+)/")
matchObject = numRegex.search(countText)
numOfComics = int(matchObject.group(1))
logging.debug(f"Number of comics = {numOfComics}")


# Allowing the option of downloading a specific number of latest comics through CL arguments.
# Give no CL arguments to download all comics.
if len(sys.argv) > 1:
    NUM_TO_DOWNLOAD = int(sys.argv[1])
else:
    NUM_TO_DOWNLOAD = numOfComics
logging.info(f"{NUM_TO_DOWNLOAD} comics to be downloaded.")


# Create image directory.
if not os.path.exists("XKCD Comics"):
    os.mkdir("XKCD Comics")


# Select each image , write it to disk and open the previous image.
for num in range(1, NUM_TO_DOWNLOAD + 1):
    comicNum = numOfComics - (num - 1)

    # Downloading the image.
    downloadError = False
    imageElem = xkcdSoup.select("#comic img", parser = "html.parser")
    if imageElem != []:
        imageLink = imageElem[0].get("src") 
    else:
        print(f"Could not find comic image {comicNum}")
        logging.debug(f"Could not find comic image {comicNum}")
        downloadError = True
    print(f"Downloading image {num}, comic number {comicNum}...")
    try:
        imageObject = requests.get("http:" + imageLink, timeout = (3.05, 27))
    except Exception as e:
        print(f"There was an error downloading comic {comicNum}")
        logging.debug(f"Error downloading comic {comicNum}")
        downloadError = True

    # Writing the image to disk and numbering it.
    if not downloadError:
        with open(os.path.join("XKCD Comics", "xkcd" + str(comicNum) + ".png"), "wb") as image:
            for chunk in imageObject.iter_content(1024 * 128):
                image.write(chunk)

    # Updating xkcdSoup to contain the previous comic webpage.
    prevTag = xkcdSoup.select('a[rel="prev"]', parser = "html.parser")[0]
    subLink = prevTag.get("href")
    if subLink == "#":
        logging.info("All images have been downloaded.")
        break
    prevImageLink = "http://www.xkcd.com" + subLink
    html = requests.get(prevImageLink, timeout = (3.05, 27))
    if html.status_code != 200:
        print(f"{num} images have been successfully downloaded.")
        logging.critical(f"Unexpected error occurred while downloading comic image {comicNum}")
        sys.exit("An unexpected error has occurred with the connection to the server.")
    xkcdSoup = bs4.BeautifulSoup(html.text, features = "html.parser")


# Success Message.
print(f"{num} images have been successfully downloaded.")
logging.info(f"{num} images have been successfully downloaded.")