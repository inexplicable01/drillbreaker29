import requests
import os

def download_image(url, save_path='.'):
    """
    Download an image from a given URL and save it to a specified directory.

    Parameters:
    - url (str): The URL of the image.
    - save_path (str): The directory where the image should be saved.

    Returns:
    - str: The path to the saved image.
    """

    # Send a GET request to the image URL
    response = requests.get(url, stream=True)
    response.raise_for_status()

    # Get the image's filename based on its URL
    filename = os.path.join(save_path, os.path.basename(url))

    # Write the image data to a local file
    with open(filename, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    return filename

# # List of image URLs
# image_urls = [
#     "https://photos.zillowstatic.com/fp/fd5ef8e29dcca1ade16827cbffad85b7-cc_ft_1536.jpg",
#     "https://photos.zillowstatic.com/fp/1aab7e8847e5cccea5294995428803dd-cc_ft_1536.jpg",
#     "https://photos.zillowstatic.com/fp/e1d7ce6b83f2c5e15b16c0bad11d1710-cc_ft_1536.jpg",
#     "https://photos.zillowstatic.com/fp/f7cab691a751438ead982ba95e9f9fda-cc_ft_1536.jpg",
#     "https://photos.zillowstatic.com/fp/9b221879d862f5277450c076ea2d29c3-cc_ft_1536.jpg"
# ]
#
# # Download each image
# for url in image_urls:
#     saved_path = download_image(url)
#     print(f"Downloaded {url} to {saved_path}")
