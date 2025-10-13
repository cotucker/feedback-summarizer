def main():
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    nltk.download('vader_lexicon')
    tweet = ''
    print(SentimentIntensityAnalyzer().polarity_scores(tweet))


if __name__ == "__main__":
    main()
