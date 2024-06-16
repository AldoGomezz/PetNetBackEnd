"""This script defines a function that transforms the input image into a tensor that can be used as input to the model. The function uses the PyTorch transforms module to apply the necessary transformations to the input image. The transformations include resizing the image to 255x255 pixels, cropping the image to 224x224 pixels, converting the image to a PyTorch tensor, and normalizing the image using the mean and standard deviation values used during training. The function returns the transformed image as a tensor."""

# import io
from torchvision import transforms
from torchvision import models
import torch


def transform_image(image):
    """Transform the input image into a tensor that can be used as input to the model."""
    my_transforms = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    # image = Image.open(io.BytesIO(image_bytes))
    return my_transforms(image).unsqueeze(0)


def load_model(model_path, device_name):
    """Load the model from the model_path and return the model"""
    # Loading Model and making predictions
    resnet50 = models.resnet50(weights=None)
    # Adjust the output size of the fc layer to match the output size of the saved model parameters
    num_ftrs = resnet50.fc.in_features
    resnet50.fc = torch.nn.Linear(num_ftrs, 4)

    # Load the trained model parameters
    if torch.cuda.is_available():
        resnet50.load_state_dict(torch.load(model_path))
    else:
        resnet50.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))

    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    resnet50 = resnet50.to(device=device_name)
    return resnet50


def get_prediction(image_path, model, device):
    """Get the prediction of the image using the model"""
    clases = ["dermatitis", "pioderma", "sarna", "sano"]
    # with open(image_path, "rb") as f:
    #    image_bytes = f.read()
    #    tensor = transform_image(image_bytes=image_bytes)
    #    img_transform = tensor.to(device)
    tensor = transform_image(image_path)
    img_transform = tensor.to(device)

    # Make to evaluation
    model.eval()
    output = model(img_transform)
    # Aplicando softmax para obtener las probabilidades
    probabilities = torch.nn.functional.softmax(output, dim=1)

    # Get the predicted class index
    _, predicted = torch.max(output, 1)

    # Obteniendo la probabilidad de la clase predicha
    predicted_probability = probabilities[0][predicted].item()

    # Get the predicted class name
    predicted_class = clases[predicted.item()]

    # If predicted_probability es less that 0.5, return "No se puede determinar", if is less than 0.7 return "No estoy seguro"
    if predicted_probability < 0.6:
        predicted_class = "No se puede determinar"

    return predicted_probability, predicted_class
