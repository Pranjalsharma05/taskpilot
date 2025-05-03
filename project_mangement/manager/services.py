import pandas as pd
from transformers import pipeline

# Load task descriptions from your CSV once
df = pd.read_csv("Task Catagories.csv.csv")
candidate_labels = df["Task Description"].unique().tolist()

# Load model once
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def generate_task_suggestions(description, deadline=None):
    """
    Generate AI-based task suggestions from a project description.
    Returns a list of top N task titles.
    """
    results = classifier(description, candidate_labels, multi_label=True)

    top_n = 9
    return results['labels'][:top_n]
