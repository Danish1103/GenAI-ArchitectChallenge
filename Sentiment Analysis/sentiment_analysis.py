import csv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import pandas as pd

# Azure Cognitive Service credentials
AZURE_TEXT_ANALYTICS_ENDPOINT = "<Cognitive_Service_Endpoint>"
AZURE_TEXT_ANALYTICS_KEY = "<API_KEY"

# Initialize the Text Analytics client
def authenticate_client():
    return TextAnalyticsClient(
        endpoint=AZURE_TEXT_ANALYTICS_ENDPOINT,
        credential=AzureKeyCredential(AZURE_TEXT_ANALYTICS_KEY)
    )

# Analyze sentiment for a batch of reviews
def analyze_sentiments(client, reviews):
    response = client.analyze_sentiment(documents=reviews)
    results = []
    for idx, document in enumerate(response):
        if not document.is_error:
            results.append({
                "Review": reviews[idx],
                "Sentiment": document.sentiment,
                "Positive Confidence": document.confidence_scores.positive,
                "Neutral Confidence": document.confidence_scores.neutral,
                "Negative Confidence": document.confidence_scores.negative
            })
        else:
            results.append({
                "Review": reviews[idx],
                "Sentiment": "Error",
                "Positive Confidence": 0,
                "Neutral Confidence": 0,
                "Negative Confidence": 0
            })
    return results

# Main script logic
def main(input_csv, output_csv):
    # Load reviews from CSV
    data = pd.read_csv(input_csv)
    if "Review" not in data.columns:
        print("Error: The input CSV must have a column named 'Review'.")
        return
    
    reviews = data["Review"].tolist()
    
    # Authenticate and analyze sentiments
    client = authenticate_client()
    results = analyze_sentiments(client, reviews)
    
    # Save results to a new CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_csv, index=False)
    print(f"Sentiment analysis completed. Results saved to '{output_csv}'.")

# Entry point
if __name__ == "__main__":
    input_csv_path = "Sentiment Analysis/input_reviews.csv"  # Path to your input CSV file
    output_csv_path = "output_sentiment_analysis.csv"  # Path to save the results
    main(input_csv_path, output_csv_path)