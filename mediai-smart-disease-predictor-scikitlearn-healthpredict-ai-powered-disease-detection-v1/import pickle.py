import pickle

model_path = r"D:\py3.11\medical diagonises ai\Models\diabetes_model.sav"
with open(model_path, 'rb') as file:
    diabetes_model = pickle.load(file)
