import numpy as np
import streamlit as st
import torch
import torchvision.transforms as T
import urllib
from PIL import Image
from torchvision.utils import make_grid, save_image

from model import RestorationModel
import albumentations as A
from albumentations.pytorch import ToTensorV2

CHECKPOINT = "https://github.com/Git-Nayanjyoti/image-inpainter/releases/download/v-0.0.1/weights_sun_4_jul_2021.ckpt"
CHECKPOINT2 = ""
SIZE = 256

# MODEL_WEIGHTS_DEPLOYMENT_URL = ''

# Constants for sidebar dropdown
SIDEBAR_OPTION_PROJECT_INFO = "Show Project Info"
SIDEBAR_OPTION_ENCODER_DECODER = "Auto Encoder Decoder"
SIDEBAR_OPTION_PIX2PIX = "PIX2PIX GAN"

SIDEBAR_OPTIONS = [SIDEBAR_OPTION_PROJECT_INFO, SIDEBAR_OPTION_ENCODER_DECODER, SIDEBAR_OPTION_PIX2PIX]

preprocess_fn = A.Compose([
    A.ToFloat(max_value=255.0),
    ToTensorV2(p=1.0)
])

dropout_fn = A.CoarseDropout(max_holes=1, min_holes=1, p=1.0, max_width=50, max_height=50)
resize_fn  = A.Resize(SIZE, SIZE, p=1.0)

def make_holes(image):
    image = np.array(image)
    with st.spinner(" Genrating patches over image ..."):
        aug_image = dropout_fn(image=image)['image']
    image = aug_image.astype(np.uint8)
    image = Image.fromarray(image)
    st.markdown("### Image after adding patches")
    st.image(image, caption='Image with patches')
    return aug_image

def resize_image(uploaded_image):
    image = np.array(uploaded_image)
    image = resize_fn(image=image)['image']

    display_image = image.astype(np.uint8)
    display_image = Image.fromarray(display_image)
    st.title("Here is the image you've uploaded")
    st.image(image, caption='Uploaded Image')
    return image


@ st.cache()
def load_model():
    model = RestorationModel.load_from_checkpoint(CHECKPOINT)
    model.eval()
    return model


# Inference function - TODO this could probably be improved ...
@ torch.no_grad()
def do_predict(image):
    image = np.array(image)
    with st.spinner("🏃‍♂️ Getting the latest model weights ..."):
        model = load_model()
    st.success("🚀 Model Weights Loaded Successfully !")
    image = preprocess_fn(image=image)['image']
    image = image.unsqueeze(0)
    with st.spinner("🏃‍♂️ Doing the Math 🤓 ..."):
        # add batch dimension to image
        results = model(image)
    st.success("🚀 Predictions Generated !")
    results = results.sigmoid()
    results = make_grid(results, normalize=True).permute(1, 2, 0).data.cpu().numpy()
    results *= 255.0
    results = results.astype(np.uint8)
    results = A.functional.adjust_brightness_torchvision(results, factor=1.2)
    results = A.functional.adjust_contrast_torchvision(results, factor=0.8)
    return Image.fromarray(results)

@st.cache(show_spinner=False)
def get_file_content_as_string():
    url = 'https://raw.githubusercontent.com/Git-Nayanjyoti/image-inpainter/main/Project_Info.md'
    response = urllib.request.urlopen(url)
    return response.read().decode("utf-8")


# fmt: off
def main():
    title = """
    # Image Inpainter
    """
    
    st.markdown(title)
    st.write(" --------- ")

    st.sidebar.warning("Please upload SINGLE-person images. For best results, also center the person in the image")
    st.sidebar.write(" -------- ")
    st.sidebar.title("Browse the Following")

    app_mode = st.sidebar.selectbox("Please select from the following", SIDEBAR_OPTIONS)

    if app_mode == SIDEBAR_OPTION_PROJECT_INFO:
        st.sidebar.write(" ------- ")
        st.sidebar.success("Project information showing on the right!")
        st.write(get_file_content_as_string())
        st.write("Our goal is to retrieve images that have faced the wrath of time and got degraded")
        st.info("👈Please select a Model to test")

    elif app_mode == SIDEBAR_OPTION_ENCODER_DECODER:
        st.write("Auto Encoder Decoder")
        st.sidebar.success("Try our Auto Encoder Decoder model on the right!")
        uploaded_image = st.file_uploader("Upload An Image", type=["jpg", "png", "jpeg"])

        if uploaded_image is not None:
           image = Image.open(uploaded_image)
           image = resize_image(image)
           image = make_holes(image)
           predictions = do_predict(image)
           st.image(predictions, caption='restored image')
    else:
        st.sidebar.success("Try our PIX2PIX model on the right!")
        st.write("pix2pix GAN")
        uploaded_image_gan = st.file_uploader("Upload An Image", type=["jpg", "png", "jpeg"])

        if uploaded_image_gan is not None:
            image_gan = Image.open(uploaded_image_gan)
            image_gan = resize_image(image_gan)
            image_gan = make_holes(image_gan)
           



    

if __name__ == "__main__":
    # run the app
    main()
    about_expander = st.beta_expander("More About Our Porject")
    about_expander.write("Hi there! If you have any question about our porject, or simply want to check out the source code, please visit our github repo: https://github.com/Git-Nayanjyoti/image-inpainter.git")