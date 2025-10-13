import pandas as pd
import nltk


def main():
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    nltk.download('vader_lexicon')
    tweet = 'hello darling'
    print(SentimentIntensityAnalyzer().polarity_scores(tweet))    


def load_dataset():
    df = pd.read_csv('data/sentiment-analysis.csv')
    print(df.info())                                                                 
    print(df.head())    

    df['Text, Sentiment, Source, Date/Time, User ID, Location, Confidence Score'] = (
        df['Text, Sentiment, Source, Date/Time, User ID, Location, Confidence Score']
        .fillna('"",,,,,,')
        .astype(str)
    )                                                            
    data_list = df['Text, Sentiment, Source, Date/Time, User ID, Location, Confidence Score'].values.tolist()
    
    print(data_list[:5])

    segmented_data_list = [data.split(',') for data in data_list]



    print(segmented_data_list[0])

    text_list = [segmented_data[0][1:-1] for segmented_data in segmented_data_list]
    score_list = [segmented_data[6] for segmented_data in segmented_data_list]

    data_dict = {
        'Text' : text_list,
        'Sentiments' : [segmented_data[1] for segmented_data in segmented_data_list],
        'Source' : [segmented_data[2] for segmented_data in segmented_data_list],
        'Data/Time' : [segmented_data[3] for segmented_data in segmented_data_list],
        'User ID' : [segmented_data[4] for segmented_data in segmented_data_list],
        'Location' : [segmented_data[5] for segmented_data in segmented_data_list],
        'Confidence Score' : score_list

    }

    new_df = pd.DataFrame(data_dict)

    new_df.to_csv('data/data.csv')

    print(new_df.head())


if __name__ == "__main__":                                                              
    load_dataset()
